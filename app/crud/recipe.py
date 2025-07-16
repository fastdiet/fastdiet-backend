from sqlalchemy.orm import Session, selectinload
from app.crud.cuisine_region import get_or_create_cuisine_region
from app.crud.diet_type import get_or_create_diet_type
from app.crud.dish_type import get_or_create_dish_type
from app.crud.ingredient import get_or_create_spoonacular_ingredient
from app.crud.nutrient import get_or_create_nutrient
from app.models.recipe import Recipe
from app.models.recipes_cuisine import RecipesCuisine
from app.models.recipes_diet_type import RecipesDietType
from app.models.recipes_dish_type import RecipesDishType
from app.models.recipes_ingredient import RecipesIngredient
from app.models.recipes_nutrient import RecipesNutrient


def get_recipe_by_id(db: Session, recipe_id: int) -> Recipe | None:
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()

def get_recipes_by_creator_id(db: Session, creator_id: int) -> list[Recipe]:
    return db.query(Recipe).filter(Recipe.creator_id == creator_id).all()

def get_recipe_details(db: Session, recipe_id: int) -> Recipe | None:
    return (
        db.query(Recipe)
        .filter(Recipe.id == recipe_id)
        .options(
            selectinload(Recipe.recipes_cuisines).joinedload(RecipesCuisine.cuisine),
            selectinload(Recipe.recipes_dish_types).joinedload(RecipesDishType.dish_type),
            selectinload(Recipe.recipes_diet_types).joinedload(RecipesDietType.diet_type),
            selectinload(Recipe.recipes_ingredients).joinedload(RecipesIngredient.ingredient),
            selectinload(Recipe.recipes_nutrients).joinedload(RecipesNutrient.nutrient)
        )
        .first()
    )

def _create_recipe_relationships(db: Session, recipe_id: int, items: list, get_or_create_func: callable, model_class: type, foreign_key_name: str):
    if not items:
        return []
    
    associations = []
    for name in items:
        related_obj = get_or_create_func(db, name)
        if related_obj:
            association = model_class(recipe_id=recipe_id)
            setattr(association, foreign_key_name, related_obj.id)
            associations.append(association)

    return associations

def _create_recipe_nutrients(db: Session, recipe_id: int, nutrients_data: list) -> list[RecipesNutrient]:
    if not nutrients_data:
        return []
    
    primary_nutrients = {"calories", "fat", "saturated fat", "carbohydrates", "net carbohydrates", "sugar", "protein", "fiber"}
    recipe_nutrients = []
    for nutrient_data in nutrients_data:
        name = nutrient_data.get("name")
        if name and nutrient_data.get("amount") is not None:
            is_primary = name.lower() in primary_nutrients
            db_nutrient = get_or_create_nutrient(db, name, is_primary=is_primary)
            if db_nutrient:
                recipe_nutrients.append(RecipesNutrient(
                    recipe_id=recipe_id,
                    nutrient_id=db_nutrient.id,
                    amount=nutrient_data["amount"],
                    unit=nutrient_data.get("unit")
                ))
    return recipe_nutrients

def _create_recipe_ingredients(db: Session, recipe_id: int, ingredients_data: list) -> list[RecipesIngredient]:
    if not ingredients_data:
        return []

    recipe_ingredients = []
    for ing_data in ingredients_data:
        db_ingredient = get_or_create_spoonacular_ingredient(db, ing_data)
        if db_ingredient:
            amount = ing_data.get("measures", {}).get("metric", {}).get("amount", ing_data.get("amount", 0.0))
            unit = ing_data.get("measures", {}).get("metric", {}).get("unitShort", ing_data.get("unit"))

            recipe_ingredients.append(RecipesIngredient(
                recipe_id=recipe_id,
                ingredient_id=db_ingredient.id,
                original_ingredient_name=ing_data.get("original", ing_data.get("originalName")),
                amount=amount,
                unit=unit,
                measures_json=ing_data.get("measures")
            ))
    return recipe_ingredients

def get_or_create_spoonacular_recipe(db: Session, recipe_data: dict):

    calories = None
    for nutrient in recipe_data.get("nutrition", {}).get("nutrients", []):
        if nutrient.get("name", "").lower() == "calories":
            calories = nutrient.get("amount")
            break

    recipe = db.query(Recipe).filter_by(spoonacular_id=recipe_data["id"]).first()
    if recipe:
        recipe.title = recipe_data.get("title", recipe.title)
        recipe.summary = recipe_data.get("summary", recipe.summary)
        recipe.image_url = recipe_data.get("image", recipe.image_url)
        recipe.calories = calories if calories is not None else recipe.calories

        db.commit()
        return get_recipe_details(db, recipe.id)
    
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
    db.add(new_recipe)
    db.flush()

    all_associations = []
    all_associations.extend(_create_recipe_relationships(db, new_recipe.id, recipe_data.get("cuisines"), get_or_create_cuisine_region, RecipesCuisine, 'cuisine_id'))
    all_associations.extend(_create_recipe_relationships(db, new_recipe.id, recipe_data.get("dishTypes"), get_or_create_dish_type, RecipesDishType, 'dish_type_id'))
    all_associations.extend(_create_recipe_relationships(db, new_recipe.id, recipe_data.get("diets"), get_or_create_diet_type, RecipesDietType, 'diet_type_id'))
    all_associations.extend(_create_recipe_nutrients(db, new_recipe.id, recipe_data.get("nutrition", {}).get("nutrients", [])))
    all_associations.extend(_create_recipe_ingredients(db, new_recipe.id, recipe_data.get("extendedIngredients")))

    if all_associations:
        db.add_all(all_associations)
               
    return new_recipe


