from fastapi import HTTPException
from app.core.errors import ErrorCode
from app.crud.ingredient import get_or_create_ingredient_by_name
from app.crud.recipe import get_recipe_details
from app.models.ingredient import Ingredient
from app.models.nutrient import Nutrient
from app.models.recipe import Recipe
from sqlalchemy.orm import Session

from app.models.recipes_ingredient import RecipesIngredient
from app.schemas.recipe import RecipeCreate


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


def create_recipe_from_user_input(db: Session, recipe_data: RecipeCreate, user_id: int) -> Recipe:

    analyzed_instructions = [step.model_dump() for step in recipe_data.analyzed_instructions] if recipe_data.analyzed_instructions else None
    new_recipe = Recipe(
        title=recipe_data.title.strip(),
        summary=recipe_data.summary.strip() if recipe_data.summary else None,
        image_url=recipe_data.image_url.strip() if recipe_data.image_url else None,
        ready_min=recipe_data.ready_min,
        servings=recipe_data.servings,
        creator_id=user_id,
        analyzed_instructions=[{
            "steps": analyzed_instructions
        }]
    )
    db.add(new_recipe)
    db.flush()

    recipes_ingredients = []
    unique_ingredients = set()

    for ing in recipe_data.ingredients:
        normalized = ing.name.strip().lower()
        if normalized in unique_ingredients:
            raise HTTPException(
                status_code=400,
                detail={"code": ErrorCode.DUPLICATED_INGREDIENT, "message": f"Duplicated ingredient in request: '{normalized}'"}
            )
        
        unique_ingredients.add(normalized)
        db_ingredient = get_or_create_ingredient_by_name(db, ing.name)

        recipes_ingredients.append(RecipesIngredient(
            recipe_id=new_recipe.id,
            ingredient_id=db_ingredient.id,
            amount=ing.amount,
            unit=ing.unit
        ))
    
    db.add_all(recipes_ingredients)

    db.commit()
    full_recipe = get_recipe_details(db, new_recipe.id)
    
    return full_recipe