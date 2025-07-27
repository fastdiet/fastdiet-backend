from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload
from app.crud.cuisine_region import get_or_create_cuisine_region
from app.crud.dish_type import get_or_create_dish_type
from app.crud.ingredient import get_or_create_spoonacular_ingredient
from app.crud.nutrient import get_or_create_nutrient
from app.models.cuisine_region import CuisineRegion
from app.models.dish_type import DishType
from app.models.recipe import Recipe
from app.models.recipes_diet_type import RecipesDietType
from app.models.recipes_dish_type import RecipesDishType
from app.models.recipes_ingredient import RecipesIngredient
from app.models.recipes_nutrient import RecipesNutrient
from app.models.user_preferences import UserPreferences

from app.services.diet_types import get_or_create_diet_objects
from app.services.meal_plan_generator import MealPlanConfig, MealSlot


def get_recipe_by_id(db: Session, recipe_id: int) -> Recipe | None:
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()

def get_recipes_by_creator_id(db: Session, creator_id: int) -> list[Recipe]:
    return (
        db.query(Recipe)
        .options(selectinload(Recipe.dish_types))
        .filter(Recipe.creator_id == creator_id)
        .all()
    )

def get_recipe_details(db: Session, recipe_id: int) -> Recipe | None:
    return (
        db.query(Recipe)
        .filter(Recipe.id == recipe_id)
        .options(
           selectinload(Recipe.cuisines),
            selectinload(Recipe.dish_types),
            selectinload(Recipe.diet_types),
            selectinload(Recipe.recipes_ingredients).joinedload(RecipesIngredient.ingredient),
            selectinload(Recipe.recipes_nutrients).joinedload(RecipesNutrient.nutrient)
        )
        .first()
    )

def get_recipe_suggestions_from_db(
    db: Session, exclude_recipe_ids: set[int], preferences: UserPreferences, min_calories: float, max_calories: float, limit: int, meal_slot: MealSlot
):

    query = db.query(Recipe).filter(
        Recipe.id.notin_(exclude_recipe_ids),
        Recipe.calories.between(min_calories, max_calories),
        Recipe.spoonacular_id.isnot(None),
        Recipe.creator_id.is_(None),
    )

    desired_dish_type = "Breakfast" if meal_slot == MealSlot.BREAKFAST else "Main course"

    # Filter by dish type
    query = query.join(RecipesDishType).join(DishType).filter(DishType.name == desired_dish_type)
    
    # Filter by diet
    if preferences.diet_type_id != MealPlanConfig.BALANCE_DIET_ID:
        if preferences.diet_type_id == MealPlanConfig.VEGETARIAN_DIET_ID:
            query = query.join(RecipesDietType, isouter=True).filter(
                or_(
                    RecipesDietType.diet_type_id == preferences.diet_type_id,
                    Recipe.vegetarian == True,
                    Recipe.vegan
                )
            )
        elif preferences.diet_type_id == MealPlanConfig.VEGAN_DIET_ID:
            query = query.join(RecipesDietType, isouter=True).filter(
                or_(
                    RecipesDietType.diet_type_id == preferences.diet_type_id,
                    Recipe.vegan == True
                )
            )
        elif preferences.diet_type_id == MealPlanConfig.GLUTEN_FREE_DIET_ID:
            query = query.join(RecipesDietType, isouter=True).filter(
                or_(
                    RecipesDietType.diet_type_id == preferences.diet_type_id,
                    Recipe.gluten_free == True
                )
            )
        else:
            query = query.join(RecipesDietType).filter(RecipesDietType.diet_type_id == preferences.diet_type_id)

    # Filter by intolerances
    if preferences.intolerances:
        for intolerance_obj in preferences.intolerances:
            intolerance_name = intolerance_obj.name.lower()
            if 'gluten' in intolerance_name:
                query = query.filter(Recipe.gluten_free == True)
            if 'dairy' in intolerance_name:
                query = query.filter(Recipe.dairy_free == True)

    # Filter by cuisines
    if preferences.cuisines:
        cuisine_ids = [cuisine.id for cuisine in preferences.cuisines]
        query = query.join(Recipe.cuisines).filter(CuisineRegion.id.in_(cuisine_ids))

    return query.distinct().order_by(func.random()).limit(limit).all()
    

def _create_recipe_nutrients(db: Session, recipe_id: int, nutrients_data: list) -> list[RecipesNutrient]:
    if not nutrients_data:
        return []
    
    primary_nutrients = {"calories", "fat", "saturated fat", "carbohydrates", "net carbohydrates", "sugar", "protein", "fiber"}
    recipe_nutrients = []
    processed_nutrient_ids = set()
    for nutrient_data in nutrients_data:
        name = nutrient_data.get("name")
        if name and nutrient_data.get("amount") is not None:
            is_primary = name.lower() in primary_nutrients
            db_nutrient = get_or_create_nutrient(db, name, is_primary=is_primary)
            if db_nutrient and db_nutrient.id not in processed_nutrient_ids:
                recipe_nutrients.append(RecipesNutrient(
                    recipe_id=recipe_id,
                    nutrient_id=db_nutrient.id,
                    amount=nutrient_data["amount"],
                    unit=nutrient_data.get("unit")
                ))
                processed_nutrient_ids.add(db_nutrient.id)
    return recipe_nutrients

def _create_recipe_ingredients(db: Session, recipe_id: int, ingredients_data: list) -> list[RecipesIngredient]:
    if not ingredients_data:
        return []

    recipe_ingredients = []
    processed_ingredient_ids = set()
    for ing_data in ingredients_data:
        db_ingredient = get_or_create_spoonacular_ingredient(db, ing_data)
        if db_ingredient and db_ingredient.id not in processed_ingredient_ids:
            metric_data = ing_data.get("measures", {}).get("metric") or {}
            amount = metric_data.get("amount", ing_data.get("amount", 0.0))
            unit = metric_data.get("unitShort", ing_data.get("unit"))

            recipe_ingredients.append(RecipesIngredient(
                recipe_id=recipe_id,
                ingredient_id=db_ingredient.id,
                original_ingredient_name=ing_data.get("original", ing_data.get("originalName")),
                amount=amount,
                unit=unit,
                measures_json=ing_data.get("measures")
            ))
            processed_ingredient_ids.add(db_ingredient.id)
    return recipe_ingredients

def get_or_create_spoonacular_recipe(db: Session, recipe_data: dict):

    recipe = db.query(Recipe).filter_by(spoonacular_id=recipe_data["id"]).first()
    if recipe:
        return recipe
    
    calories = None
    for nutrient in recipe_data.get("nutrition", {}).get("nutrients", []):
        if nutrient.get("name", "").lower() == "calories":
            calories = nutrient.get("amount")
            break
    
    new_recipe = Recipe(
        spoonacular_id=recipe_data["id"],
        title=recipe_data.get("title"),
        image_url=recipe_data.get("image"),
        image_type=recipe_data.get("imageType"),
        ready_min=recipe_data.get("readyInMinutes"),
        servings=recipe_data.get("servings"),
        summary=recipe_data.get("summary"),
        vegetarian=recipe_data.get("vegetarian"),
        vegan=recipe_data.get("vegan"),
        gluten_free=recipe_data.get("glutenFree"),
        dairy_free=recipe_data.get("dairyFree"),
        very_healthy=recipe_data.get("veryHealthy"),
        cheap=recipe_data.get("cheap"),
        very_popular=recipe_data.get("veryPopular"),
        sustainable=recipe_data.get("sustainable"),
        low_fodmap=recipe_data.get("lowFodmap"),
        preparation_min=recipe_data.get("preparationMinutes"),
        cooking_min=recipe_data.get("cookingMinutes"),
        calories= calories,
        analyzed_instructions=recipe_data.get("analyzedInstructions")
    )

    dish_type_names = set(recipe_data.get("dishTypes", []))
    if dish_type_names:
        dish_type_objects = [get_or_create_dish_type(db, name) for name in dish_type_names]
        new_recipe.dish_types = [obj for obj in dish_type_objects if obj is not None]
    
    cuisine_names = set(recipe_data.get("cuisines", []))
    if cuisine_names:
        cuisine_objects = [get_or_create_cuisine_region(db, name) for name in cuisine_names]
        new_recipe.cuisines = [obj for obj in cuisine_objects if obj is not None]

    api_diets = recipe_data.get("diets", [])
    if api_diets:
        new_recipe.diet_types = get_or_create_diet_objects(db, api_diets)


    db.add(new_recipe)
    db.flush()

    all_associations = []
    all_associations.extend(_create_recipe_nutrients(db, new_recipe.id, recipe_data.get("nutrition", {}).get("nutrients", [])))
    all_associations.extend(_create_recipe_ingredients(db, new_recipe.id, recipe_data.get("extendedIngredients")))

    if all_associations:
        db.add_all(all_associations)
               
    return new_recipe

