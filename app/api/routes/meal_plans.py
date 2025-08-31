import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.errors import ErrorCode
from app.crud.meal_item import create_db_meal_item, get_complete_meal_item_by_id, get_meal_item_by_id
from app.crud.meal_plan import get_latest_meal_plan_for_user, get_meal_plan_by_id
from app.crud.recipe import get_recipe_by_id
from app.crud.user_preferences import get_user_preferences_by_user_id
from app.db.db_connection import get_db
from app.core.auth import get_current_user, get_language
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.meal_plan import MealItemCreate, MealPlanResponse, GeneratedMealResponse, SlotMealResponse
from app.schemas.recipe import RecipeId, RecipeShort
from app.services.meal_plan import generate_meal_plan_for_user, get_meal_replacement_suggestions, meal_plan_to_response
from app.services.recipe import serialize_recipe_short, serialize_recipe_short_list
from app.services.spoonacular import SpoonacularService


logger = logging.getLogger(__name__)

router = APIRouter(tags=["meal_plans"], prefix="/meal_plans")

@router.post("/generate", response_model=GeneratedMealResponse)
async def generate_meal_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_language)
):
    """Endpoint to generate a meal plan for the user"""
    logger.info(f"Meal plan generation requested by user ID: {current_user.id} ({current_user.username})")
    db_meal_plan, status = await generate_meal_plan_for_user(db, current_user.id)
    meal_plan_response = meal_plan_to_response(db_meal_plan, lang)
    logger.info(f"Meal plan generation for user ID {current_user.id} completed with status: {status.value}")
    return GeneratedMealResponse(
        meal_plan=meal_plan_response,
        status=status.value
    )

    
@router.get("/me", response_model=MealPlanResponse)
def get_my_meal_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_language)
):
    """Endpoint to get the current user's meal plan (if exists)"""
  
    logger.info(f"Fetching meal plan for user ID: {current_user.id} ({current_user.username})")
    meal_plan = get_latest_meal_plan_for_user(db, current_user.id)
    if not meal_plan:
        logger.warning(f"No meal plan found for user ID: {current_user.id} ({current_user.username})")
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.MEAL_PLAN_NOT_FOUND, "message": "No meal plan found for this user"}
        )
    return meal_plan_to_response(meal_plan, lang)


@router.get("/suggestions", response_model=list[RecipeShort])
async def get_meal_suggestions(
    meal_item_id: int | None = Query(None),
    day_index: int | None = Query(None, ge=0, le=6),
    slot: int | None = Query(None, ge=0),
    meal_type: str | None = Query(None),
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_language)
):
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is requesting meal suggestions.")
    preferences = get_user_preferences_by_user_id(db, current_user.id)
    if not preferences:
        logger.warning(f"Suggestions request failed for user ID {current_user.id} ({current_user.username}): Preferences not found.")
        raise HTTPException(status_code=404, detail="User preferences not found")
    
    type_to_search = None
    meal_to_replace = None
    if meal_item_id:
        logger.info(f"Getting suggestions to replace meal_item_id: {meal_item_id}")
        db_meal_item = get_complete_meal_item_by_id(db, meal_item_id)
        
        if not db_meal_item:
            logger.warning(f"Suggestions request failed: Meal item ID {meal_item_id} not found.")
            raise HTTPException(status_code=404, detail={"code": ErrorCode.MEAL_ITEM_NOT_FOUND, "message": "Meal item not found"})

        if db_meal_item.meal_plan.user_id != current_user.id:
            logger.error(f"FORBIDDEN access attempt by user ID {current_user.id} on meal item ID {meal_item_id}.")
            raise HTTPException(status_code=403, detail={"code": ErrorCode.MEAL_ITEM_ACCESS_DENIED, "message": "User does not have access to this meal item"})
        
        type_to_search = db_meal_item.meal_type
        meal_to_replace = db_meal_item
        
    elif day_index is not None and slot is not None and meal_type is not None:
        logger.info(f"Getting suggestions for an empty slot: day {day_index}, slot {slot}, type {meal_type}")
        type_to_search = meal_type
    else:
        logger.warning(f"Bad request for suggestions from user ID {current_user.id}({current_user.username}): incorrect parameters.")
        raise HTTPException(status_code=400, detail="Either meal_item_id or (day_index and slot) must be provided")
    
    recipe_suggestions = await get_meal_replacement_suggestions(db, preferences, meal_to_replace, type_to_search, limit )
        
    return serialize_recipe_short_list(recipe_suggestions, lang)

@router.post("/meal_items", response_model=SlotMealResponse, status_code=201)
def create_meal_item(
    meal_item_data: MealItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = Depends(get_language)
):
    logger.info(f"User ID: {current_user.id} ({current_user.username}) attempting to create meal item")
    db_meal_plan = get_meal_plan_by_id(db, meal_item_data.meal_plan_id)
    if not db_meal_plan:
        logger.warning(f"Create meal item request failed: Meal plan ID {meal_item_data.meal_plan_id} not found.")
        raise HTTPException(status_code=404, detail={"code": ErrorCode.MEAL_PLAN_NOT_FOUND, "message": "Meal plan not found"})
    
    if db_meal_plan.user_id != current_user.id:
        logger.error(f"FORBIDDEN access attempt by user ID {current_user.id} on meal plan ID {meal_item_data.meal_plan_id}.")
        raise HTTPException(status_code=403, detail={"code": ErrorCode.MEAL_PLAN_ACCESS_DENIED, "message": "You do not have access to this meal plan"})
        
    db_recipe = get_recipe_by_id(db, meal_item_data.recipe_id)
    if not db_recipe:
        logger.warning(f"Create meal item request failed: Recipe ID {meal_item_data.recipe_id} not found.")
        raise HTTPException(status_code=404, detail={"code": ErrorCode.RECIPE_NOT_FOUND, "message": "Recipe plan not found"})
    
    new_meal_item = create_db_meal_item(
        db,
        meal_item_data.meal_plan_id,
        meal_item_data.recipe_id,
        meal_item_data.day_index,
        meal_item_data.slot,
        meal_item_data.meal_type
    )

    logger.info(f"Meal item {new_meal_item.id} successfully created for user ID: {current_user.id} ({current_user.username})")

    translated_recipe = serialize_recipe_short(db_recipe, lang)
    
    return SlotMealResponse(
        meal_item_id=new_meal_item.id,
        recipe=translated_recipe,
        slot=new_meal_item.slot,
        meal_type=new_meal_item.meal_type
    )


@router.patch("/meal_items/{meal_item_id}", response_model=SuccessResponse)
def change_meal_item_recipe(
    meal_item_id: int,
    new_recipe: RecipeId,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(f"User ID: {current_user.id} ({current_user.username}) attempting to change meal item {meal_item_id} to recipe {new_recipe.new_recipe_id}")
    db_meal_item = get_meal_item_by_id(db, meal_item_id)
    
    if not db_meal_item:
        logger.warning(f"Change meal item request failed: Meal item ID {meal_item_id} not found.")
        raise HTTPException(status_code=404, detail={"code": ErrorCode.MEAL_ITEM_NOT_FOUND, "message": "Meal item not found"})

    if db_meal_item.meal_plan.user_id != current_user.id:
        logger.error(f"FORBIDDEN access attempt by user ID {current_user.id} on meal item ID {meal_item_id}.")
        raise HTTPException(status_code=403, detail={"code": ErrorCode.MEAL_ITEM_ACCESS_DENIED, "message": "You do not have access to this meal item"})
    
    db_recipe = get_recipe_by_id(db, new_recipe.new_recipe_id)
    if not db_recipe:
        logger.warning(f"Change meal item request failed: Recipe ID {new_recipe.new_recipe_id} not found.")
        raise HTTPException(status_code=404, detail={"code": ErrorCode.RECIPE_NOT_FOUND, "message": "Recipe not found"})
    
    if not db_recipe.spoonacular_id and db_recipe.creator_id != current_user.id:
        logger.error(f"FORBIDDEN access attempt by user ID {current_user.id} on recipe ID {db_recipe.id}.")
        raise HTTPException(status_code=403, detail={"code": ErrorCode.RECIPE_ACCESS_DENIED, "message": "You do not have access to this recipe"})
    
    db_meal_item.recipe_id = new_recipe.new_recipe_id
    db.commit()
    logger.info(f"Meal item {meal_item_id} successfully changed for user ID: {current_user.id} ({current_user.username})")
    return SuccessResponse(success=True, message="Meal changed successfully")


@router.delete("/meal_items/{meal_item_id}", response_model=SuccessResponse)
def delete_recipe_from_meal_plan(
    meal_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to delete a recipe from the user's meal plan"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) attempting to delete meal item {meal_item_id}")
    db_meal_item = get_meal_item_by_id(db, meal_item_id)
    
    if not db_meal_item:
        logger.warning(f"Delete meal item request failed: Meal item ID {meal_item_id} not found.")
        raise HTTPException(status_code=404, detail={"code": ErrorCode.MEAL_ITEM_NOT_FOUND, "message": "Meal item not found"})
    
    if db_meal_item.meal_plan.user_id != current_user.id:
        logger.error(f"FORBIDDEN access attempt by user ID {current_user.id} on meal item ID {meal_item_id}.")
        raise HTTPException(status_code=403, detail={"code": ErrorCode.MEAL_ITEM_ACCESS_DENIED, "message": "You do not have access to this meal item"})

    db.delete(db_meal_item)
    db.commit()
    
    logger.info(f"Meal item {meal_item_id} successfully deleted for user ID: {current_user.id} ({current_user.username})")
    return SuccessResponse(success=True, message="Recipe removed successfully from the meal plan")

@router.get("/recipe", response_model=dict)
async def get_random_recipe(
    db: Session = Depends(get_db),
):
    spoonacular = SpoonacularService()
    recipes = await spoonacular.search_recipes(
        cuisine="Thai",
        type="",
        diet="pescatarian",
        intolerances="Sesame, Grain",
        sort="",
        number=1
    )

    return recipes









   