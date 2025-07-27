from fastapi import HTTPException
from app.core.errors import ErrorCode
from app.crud.dish_type import get_dish_type_by_name
from app.crud.ingredient import get_or_create_ingredient_by_name
from app.crud.recipe import get_recipe_details
from app.models.recipe import Recipe
from sqlalchemy.orm import Session
from app.models.recipes_ingredient import RecipesIngredient
from app.schemas.recipe import RecipeCreate



def create_recipe_from_user_input(db: Session, recipe_data: RecipeCreate, user_id: int) -> Recipe:

    analyzed_instructions = [step.model_dump() for step in recipe_data.analyzed_instructions] if recipe_data.analyzed_instructions else None
    new_recipe = Recipe(
        title=recipe_data.title.strip(),
        summary=recipe_data.summary.strip() if recipe_data.summary else None,
        image_url=recipe_data.image_url.strip() if recipe_data.image_url else None,
        ready_min=recipe_data.ready_min,
        servings=recipe_data.servings,
        creator_id=user_id,
        analyzed_instructions=[{"steps": analyzed_instructions}] if analyzed_instructions else None
    )
    db.add(new_recipe)
    db.flush()

    if recipe_data.dish_types:
        dish_type_objects = []
        for name in set(recipe_data.dish_types):
            db_dish_type = get_dish_type_by_name(db, name)
            if not db_dish_type:
                raise HTTPException(
                    status_code=404,
                    detail={"code": ErrorCode.DISH_TYPE_NOT_FOUND, "message": f"Dish type '{name}' not found."}
                )
            dish_type_objects.append(db_dish_type)
        new_recipe.dish_types = dish_type_objects

    recipes_ingredients = []
    unique_ingredients = set()

    for ing in recipe_data.ingredients:
        normalized_ing = ing.name.strip().lower()
        if normalized_ing in unique_ingredients:
            raise HTTPException(
                status_code=400,
                detail={"code": ErrorCode.DUPLICATED_INGREDIENT, "message": f"Duplicated ingredient in request: '{normalized_ing}'"}
            )
        
        unique_ingredients.add(normalized_ing)
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


def update_recipe_in_db(db: Session, db_recipe: Recipe, recipe_data: RecipeCreate) -> Recipe:
    
    db_recipe.title = recipe_data.title.strip()
    db_recipe.summary = recipe_data.summary.strip() if recipe_data.summary else None
    db_recipe.image_url = recipe_data.image_url.strip() if recipe_data.image_url else None
    db_recipe.ready_min = recipe_data.ready_min
    db_recipe.servings = recipe_data.servings

    if recipe_data.analyzed_instructions:
        analyzed_instructions = [step.model_dump() for step in recipe_data.analyzed_instructions]
        db_recipe.analyzed_instructions = [{"steps": analyzed_instructions}]
    else:
        db_recipe.analyzed_instructions = None


    if recipe_data.dish_types is not None:
        dish_type_objects = []
        if recipe_data.dish_types:
            for name in set(recipe_data.dish_types):
                db_dish_type = get_dish_type_by_name(db, name)
                if not db_dish_type:
                    raise HTTPException(
                        status_code=404,
                        detail={"code": ErrorCode.DISH_TYPE_NOT_FOUND, "message": f"Dish type '{name}' not found."}
                    )
                dish_type_objects.append(db_dish_type)
        db_recipe.dish_types = dish_type_objects


    db.query(RecipesIngredient).filter(RecipesIngredient.recipe_id == db_recipe.id).delete(synchronize_session=False)

    if recipe_data.ingredients: 
        new_recipes_ingredients = []
        unique_ingredients = set()
        for ing in recipe_data.ingredients:
            normalized_ing = ing.name.strip().lower()
            if normalized_ing in unique_ingredients:
                raise HTTPException(
                    status_code=400,
                    detail={"code": ErrorCode.DUPLICATED_INGREDIENT, "message": f"Duplicated ingredient in request: '{normalized_ing}'"}
                )
            unique_ingredients.add(normalized_ing)
            
            db_ingredient = get_or_create_ingredient_by_name(db, ing.name)
            new_recipes_ingredients.append(RecipesIngredient(
                recipe_id=db_recipe.id,
                ingredient_id=db_ingredient.id,
                amount=ing.amount,
                unit=ing.unit
            ))
        
        db.add_all(new_recipes_ingredients)

    db.commit()
    full_recipe = get_recipe_details(db, db_recipe.id)
    
    return full_recipe
