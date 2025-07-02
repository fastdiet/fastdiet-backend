from app.models.ingredient import Ingredient
from app.models.nutrient import Nutrient
from app.models.recipe import Recipe


def recipe_to_response(db_recipe: Recipe) -> dict:
    ingredients_response = []
    if db_recipe.recipes_ingredients:
        for assoc in db_recipe.recipes_ingredients:
            ingredient: Ingredient = assoc.ingredient
            if ingredient:
                ingredients_response.append(
                    {
                        "original_ingredient_name": assoc.original_ingredient_name,
                        "amount": assoc.amount,
                        "unit": assoc.unit,
                        "measures_json": assoc.measures_json,
                        "ingredient": {
                            "id": ingredient.id,
                            "name": ingredient.name,
                            "image_filename": ingredient.image_filename,
                            "aisle": ingredient.aisle
                        }
                    }
                )

    nutrients_response = []
    if db_recipe.recipes_nutrients:
        for assoc in db_recipe.recipes_nutrients:
            nutrient: Nutrient = assoc.nutrient
            if nutrient:
                nutrients_response.append(
                    {
                        "name": nutrient.name,
                        "amount": assoc.amount,
                        "unit": assoc.unit,
                        "is_primary": nutrient.is_primary
                    }
                )
    
    cuisines_response = [assoc.cuisine.name for assoc in db_recipe.recipes_cuisines if assoc.cuisine]
    dish_types_response = [assoc.dish_type.name for assoc in db_recipe.recipes_dish_types if assoc.dish_type]
    diets_response = [assoc.diet_type.name for assoc in db_recipe.recipes_diet_types if assoc.diet_type]

    #RecipeDetailResponse

    return {
        "id": db_recipe.id,
        "spoonacular_id": db_recipe.spoonacular_id,
        "title": db_recipe.title,
        "image_url": db_recipe.image_url,
        "image_type": db_recipe.image_type,
        "ready_min": db_recipe.ready_min,
        "servings": db_recipe.servings,
        "summary": db_recipe.summary,
        "vegetarian": db_recipe.vegetarian,
        "vegan": db_recipe.vegan,
        "gluten_free": db_recipe.gluten_free,
        "dairy_free": db_recipe.dairy_free,
        "very_healthy": db_recipe.very_healthy,
        "cheap": db_recipe.cheap,
        "very_popular": db_recipe.very_popular,
        "sustainable": db_recipe.sustainable,
        "low_fodmap": db_recipe.low_fodmap,
        "preparation_min": db_recipe.preparation_min,
        "cooking_min": db_recipe.cooking_min,
        "calories": db_recipe.calories,
        "analyzed_instructions": db_recipe.analyzed_instructions,
        "cuisines": cuisines_response,
        "dish_types": dish_types_response,
        "diets": diets_response,
        "ingredients": ingredients_response,
        "nutrients": nutrients_response
    }