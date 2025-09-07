import logging
from fastapi import HTTPException
from app.core.errors import ErrorCode
from app.crud.dish_type import get_dish_type_by_name
from app.crud.ingredient import get_or_create_ingredient_by_name
from app.crud.recipe import get_recipe_details
from app.models.recipe import Recipe
from sqlalchemy.orm import Session
from app.models.recipes_ingredient import RecipesIngredient
from app.schemas.recipe import RecipeCreate, RecipeDetailResponse, RecipeIngredientDetail, RecipeShort, RecipeUpdate
from app.services.ingredient import serialize_ingredient_short
from app.utils.translator import translate_measures_for_recipe, translate_unit_for_display


logger = logging.getLogger(__name__)

def create_recipe_from_user_input(db: Session, recipe_data: RecipeCreate, user_id: int, lang: str) -> Recipe:

    analyzed_instructions_en = None
    analyzed_instructions_es = None
    if recipe_data.analyzed_instructions:
        analyzed_instructions = [step.model_dump() for step in recipe_data.analyzed_instructions]
        analyzed_instructions_en = [{"steps": analyzed_instructions}]
        analyzed_instructions_es = [{"steps": analyzed_instructions}]
    
    title = recipe_data.title.strip()
    summary = recipe_data.summary.strip() if recipe_data.summary else None
    new_recipe = Recipe(
        title=title,
        title_es=title,
        summary=summary,
        summary_es=summary,
        image_url=recipe_data.image_url.strip() if recipe_data.image_url else None,
        ready_min=recipe_data.ready_min,
        servings=recipe_data.servings,
        creator_id=user_id,
        analyzed_instructions=analyzed_instructions_en,
        analyzed_instructions_es=analyzed_instructions_es
    )
    db.add(new_recipe)
    db.flush()

    if recipe_data.dish_types:
        dish_type_objects = []
        for name in set(recipe_data.dish_types):
            db_dish_type = get_dish_type_by_name(db, name)
            if not db_dish_type:
                logger.warning(f"Recipe creation for user {user_id} failed: Dish type '{name}' not found.")
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
            logger.warning(f"Recipe creation for user {user_id} failed: Duplicate ingredient in request: '{normalized_ing}'.")
            raise HTTPException(
                status_code=400,
                detail={"code": ErrorCode.DUPLICATED_INGREDIENT, "message": f"Duplicated ingredient in request: '{normalized_ing}'"}
            )
        
        unique_ingredients.add(normalized_ing)
        db_ingredient = get_or_create_ingredient_by_name(db, ing.name, lang)

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


def update_recipe_in_db(db: Session, db_recipe: Recipe, recipe_data: RecipeUpdate, lang: str) -> Recipe:
    
    update_data = recipe_data.model_dump(exclude_unset=True)

    if "title" in update_data:
        title = update_data["title"].strip()
        db_recipe.title = title
        db_recipe.title_es = title
    
    if "summary" in update_data:
        summary = update_data["summary"].strip() if update_data["summary"] else None
        db_recipe.summary = summary
        db_recipe.summary_es = summary

    if "image_url" in update_data:
        db_recipe.image_url = update_data["image_url"]

    if "ready_min" in update_data:
        db_recipe.ready_min = update_data["ready_min"]

    if "servings" in update_data:
        db_recipe.servings = update_data["servings"]

    if "analyzed_instructions" in update_data:
        if update_data["analyzed_instructions"]:
            analyzed_instructions = [step for step in update_data["analyzed_instructions"]]
            db_recipe.analyzed_instructions = [{"steps": analyzed_instructions}]
            db_recipe.analyzed_instructions_es = [{"steps": analyzed_instructions}]
        else:
            db_recipe.analyzed_instructions = None
            db_recipe.analyzed_instructions_es = None

    if "dish_types" in update_data:
        dish_type_objects = []
        if update_data["dish_types"]:
            for name in set(update_data["dish_types"]):
                db_dish_type = get_dish_type_by_name(db, name)
                if not db_dish_type:
                    raise HTTPException(...)
                dish_type_objects.append(db_dish_type)
        db_recipe.dish_types = dish_type_objects

    if "ingredients" in update_data:

        db.query(RecipesIngredient).filter(RecipesIngredient.recipe_id == db_recipe.id).delete(synchronize_session=False)

        if update_data["ingredients"]:
            new_recipes_ingredients = []
            unique_ingredients = set()
            for ing in recipe_data.ingredients:
                normalized_ing = ing.name.strip().lower()
                if normalized_ing in unique_ingredients:
                    logger.warning(f"Recipe update for recipe {db_recipe.id} failed: Duplicate ingredient '{normalized_ing}'.")
                    raise HTTPException(
                        status_code=400,
                        detail={"code": ErrorCode.DUPLICATED_INGREDIENT, "message": f"Duplicated ingredient in request: '{normalized_ing}'"}
                    )
                unique_ingredients.add(normalized_ing)
                
                db_ingredient = get_or_create_ingredient_by_name(db, ing.name, lang)
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


def serialize_recipe_detail(recipe: Recipe, lang: str) -> RecipeDetailResponse:
    response_data = RecipeDetailResponse.model_validate(recipe)

    if lang == "es":
        if recipe.title_es:
            response_data.title = recipe.title_es
        
        if recipe.summary_es:
            response_data.summary = recipe.summary_es

        if recipe.analyzed_instructions_es:
            response_data.analyzed_instructions = recipe.analyzed_instructions_es

    processed_ingredients = [
        RecipeIngredientDetail(
            original_ingredient_name=ri.original_ingredient_name,
            amount=ri.amount,
            unit=translate_unit_for_display(ri.unit, lang),
            measures_json=translate_measures_for_recipe(ri.measures_json, lang),
            ingredient=serialize_ingredient_short(ri.ingredient, lang),
        )
        for ri in recipe.recipes_ingredients
    ]
    response_data.ingredients = processed_ingredients

    return response_data

def serialize_recipe_short_list(recipes: list[Recipe], lang: str) -> list[RecipeShort]:
    if not recipes:
        return []
    
    serialized_recipes = []
    for recipe in recipes:
        dish_types = [dt.name.lower() for dt in recipe.dish_types]
        short_recipe = RecipeShort(
            id=recipe.id,
            spoonacular_id=recipe.spoonacular_id,
            title=recipe.title_es if lang == "es" and recipe.title_es else recipe.title,
            image_url=recipe.image_url,
            ready_min=recipe.ready_min,
            calories=recipe.calories,
            servings=recipe.servings,
            dish_types=dish_types
        )
        serialized_recipes.append(short_recipe)
        
    return serialized_recipes


def serialize_recipe_short(recipe: Recipe, lang: str) -> RecipeShort:
    
    short_recipe = RecipeShort(
        id=recipe.id,
        spoonacular_id=recipe.spoonacular_id,
        title=recipe.title_es if lang == "es" and recipe.title_es else recipe.title,
        image_url=recipe.image_url,
        ready_min=recipe.ready_min,
        calories=recipe.calories,
        servings=recipe.servings
    )
        
    return short_recipe


