from sqlalchemy.orm import Session, selectinload
from app.crud.cuisine_region import get_or_create_cuisine_region
from app.crud.diet_type import get_or_create_diet_type
from app.crud.dish_type import get_or_create_dish_type
from app.crud.ingredient import get_or_create_ingredient
from app.crud.nutrient import get_or_create_nutrient
from app.models.recipe import Recipe
from app.models.recipes_cuisine import RecipesCuisine
from app.models.recipes_diet_type import RecipesDietType
from app.models.recipes_dish_type import RecipesDishType
from app.models.recipes_ingredient import RecipesIngredient
from app.models.recipes_nutrient import RecipesNutrient


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



def get_or_create_recipe(db: Session, recipe_data: dict):
    recipe = db.query(Recipe).filter_by(spoonacular_id=recipe_data["id"]).first()

    nutrients = recipe_data.get("nutrition", {}).get("nutrients", [])
    calories_value = None

    for nutrient in nutrients:
        name = nutrient.get("name")
        amount = nutrient.get("amount")
        if name and name.lower() == "calories" and amount is not None:
            calories_value = amount
            break

    if recipe:
        recipe.title = recipe_data.get("title", recipe.title)
        recipe.summary = recipe_data.get("summary", recipe.summary)
        recipe.image_url = recipe_data.get("image", recipe.image_url)
        recipe.calories = calories_value if calories_value is not None else recipe.calories
        db.flush()
        return recipe
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
        calories= calories_value,
        analyzed_instructions=recipe_data.get("analyzedInstructions")
    )
    db.add(new_recipe)
    db.flush()

    if recipe_data.get("cuisines"):
        for cuisine_name in recipe_data["cuisines"]:
            cuisine = get_or_create_cuisine_region(db, cuisine_name)
            if cuisine:
                db_recipe_cuisine = RecipesCuisine(recipe_id=new_recipe.id, cuisine_id=cuisine.id)
                db.add(db_recipe_cuisine)

    if recipe_data.get("dishTypes"):
        for dish_type_name in recipe_data["dishTypes"]:
            dish_type = get_or_create_dish_type(db, dish_type_name)
            if dish_type:
                db_recipe_dish_type = RecipesDishType(recipe_id=new_recipe.id, dish_type_id=dish_type.id)
                db.add(db_recipe_dish_type)

    if recipe_data.get("diets"):
        for diet_name in recipe_data["diets"]:
            diet = get_or_create_diet_type(db, diet_name)
            if diet:
                db_recipe_diet = RecipesDietType(recipe_id=new_recipe.id, diet_type_id=diet.id)
                db.add(db_recipe_diet)

    primary_nutrients = ["calories", "fat", "saturated fat", "carbohydrates", "net carbohydrates", "sugar", "protein", "fiber"]
 
    for nutrient in nutrients:
        name = nutrient.get("name")
        amount = nutrient.get("amount")
        unit = nutrient.get("unit")

        if name and amount is not None and unit is not None:
            is_primary = name.lower() in primary_nutrients
            db_nutrient = get_or_create_nutrient(db, name, is_primary=is_primary)
            if db_nutrient:
                db_recipe_nutrient = RecipesNutrient(
                    recipe_id=new_recipe.id,
                    nutrient_id=db_nutrient.id,
                    amount=amount,
                    unit=unit
                )
                db.add(db_recipe_nutrient)

    if recipe_data.get("extendedIngredients"):
        for ingredient_data in recipe_data["extendedIngredients"]:
            db_ingredient = get_or_create_ingredient(db, ingredient_data)
            
            if db_ingredient:
                amount = ingredient_data.get("amount", 0.0)
                unit = ingredient_data.get("unit")
                if ingredient_data.get("measures") and ingredient_data["measures"].get("metric"):
                    amount = ingredient_data["measures"]["metric"].get("amount", 0.0)
                    unit = ingredient_data["measures"]["metric"].get("unitShort")

                existing_recipe_ingredient = db.query(RecipesIngredient).filter(
                    RecipesIngredient.recipe_id == new_recipe.id,
                    RecipesIngredient.ingredient_id == db_ingredient.id
                ).first()
                if not existing_recipe_ingredient:
                    recipe_ingredient_entry = RecipesIngredient(
                        recipe_id=new_recipe.id,
                        ingredient_id=db_ingredient.id,
                        original_ingredient_name=ingredient_data.get("original", ingredient_data.get("originalName")),
                        amount=amount,
                        unit=unit,
                        measures_json=ingredient_data.get("measures")
                    )
                    db.add(recipe_ingredient_entry)
                    db.flush()
               
    return new_recipe


