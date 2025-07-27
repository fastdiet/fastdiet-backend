from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.errors import ErrorCode
from app.crud.meal_item import create_db_meal_item, get_complete_meal_item_by_id, get_meal_item_by_id
from app.crud.meal_plan import get_latest_meal_plan_for_user, get_meal_plan_by_id
from app.crud.recipe import get_recipe_by_id
from app.crud.user_preferences import get_user_preferences_by_user_id
from app.db.db_connection import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.meal_plan import MealItemCreate, MealItemResponse, MealPlanResponse, RecipeShort
from app.schemas.recipe import RecipeId
from app.services.meal_plan import generate_meal_plan_for_user, get_meal_replacement_suggestions, meal_plan_to_response
from app.services.spoonacular import SpoonacularService


router = APIRouter(tags=["meal_plans"], prefix="/meal_plans")


@router.post("/generate", response_model=MealPlanResponse)
async def generate_meal_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to generate a meal plan for the user"""
    db_meal_plan = await generate_meal_plan_for_user(db, current_user.id)
    return meal_plan_to_response(db_meal_plan)

    
@router.get("/me", response_model=MealPlanResponse)
def get_my_meal_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to get the current user's meal plan (if exists)"""
    meal_plan = get_latest_meal_plan_for_user(db, current_user.id)
    if not meal_plan:
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.MEAL_PLAN_NOT_FOUND, "message": "No meal plan found for this user"}
        )
    return meal_plan_to_response(meal_plan)


@router.get("/suggestions", response_model=list[RecipeShort])
async def get_meal_suggestions(
    meal_item_id: int | None = Query(None),
    day_index: int | None = Query(None, ge=0, le=6),
    slot: int | None = Query(None, ge=0, le=2),
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    
    preferences = get_user_preferences_by_user_id(db, current_user.id)
    if not preferences:
        raise HTTPException(status_code=404, detail="User preferences not found")
    
    if meal_item_id:
        db_meal_item = get_complete_meal_item_by_id(db, meal_item_id)
        
        if not db_meal_item:
            raise HTTPException(status_code=404, detail={"code": ErrorCode.MEAL_ITEM_NOT_FOUND, "message": "Meal item not found"})

        if db_meal_item.meal_plan.user_id != current_user.id:
            raise HTTPException(status_code=403, detail={"code": ErrorCode.MEAL_ITEM_ACCESS_DENIED, "message": "User does not have access to this meal item"})
        
        recipe_suggestions = await get_meal_replacement_suggestions(db, preferences, db_meal_item, limit)
        
    elif day_index is not None and slot is not None:
        recipe_suggestions = await get_meal_replacement_suggestions(db, preferences, None, limit, slot)
    else:
        raise HTTPException(status_code=400, detail="Either meal_item_id or (day_index and slot) must be provided")
        

    return recipe_suggestions

@router.post("/meal_items", response_model=MealItemResponse)
def create_meal_item(
    meal_item_data: MealItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_meal_plan = get_meal_plan_by_id(db, meal_item_data.meal_plan_id)
    if not db_meal_plan:
        raise HTTPException(status_code=404, detail={"code": ErrorCode.MEAL_PLAN_NOT_FOUND, "message": "Meal plan not found"})
    
    if db_meal_plan.user_id != current_user.id:
        raise HTTPException(status_code=403, detail={"code": ErrorCode.MEAL_ITEM_ACCESS_DENIED, "message": "You do not have access to this meal item"})
        
    db_recipe = get_recipe_by_id(db, meal_item_data.recipe_id)
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    new_meal_item = create_db_meal_item(db, meal_item_data.meal_plan_id, meal_item_data.recipe_id, meal_item_data.day_index, meal_item_data.slot)
    
    return MealItemResponse(
        meal_item_id=new_meal_item.id,
        recipe=db_recipe,
        slot=new_meal_item.slot
    )


@router.patch("/meal_items/{meal_item_id}", response_model=SuccessResponse)
def change_meal_item_recipe(
    meal_item_id: int,
    new_recipe: RecipeId,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_meal_item = get_meal_item_by_id(db, meal_item_id)
    
    if not db_meal_item:
        raise HTTPException(status_code=404, detail={"code": ErrorCode.MEAL_ITEM_NOT_FOUND, "message": "Meal item not found"})

    if db_meal_item.meal_plan.user_id != current_user.id:
        raise HTTPException(status_code=403, detail={"code": ErrorCode.MEAL_ITEM_ACCESS_DENIED, "message": "You do not have access to this meal item"})
    
    db_recipe = get_recipe_by_id(db, new_recipe.new_recipe_id)
    if not db_recipe:
        raise HTTPException(status_code=404, detail={"code": ErrorCode.RECIPE_NOT_FOUND, "message": "Recipe not found"})
    
    if not db_recipe.spoonacular_id and db_recipe.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail={"code": ErrorCode.RECIPE_ACCESS_DENIED, "message": "You do not have access to this recipe"})
    
    db_meal_item.recipe_id = new_recipe.new_recipe_id
    db.commit()

    return SuccessResponse(success=True, message="Meal changed successfully")


@router.delete("/meal_items/{meal_item_id}", response_model=SuccessResponse)
def delete_recipe_from_meal_plan(
    meal_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to delete a recipe from the user's meal plan"""

    db_meal_item = get_meal_item_by_id(db, meal_item_id)
    
    if not db_meal_item:
        raise HTTPException(status_code=404, detail={"code": ErrorCode.MEAL_ITEM_NOT_FOUND, "message": "Meal item not found"})
    
    if db_meal_item.meal_plan.user_id != current_user.id:
        raise HTTPException(status_code=403, detail={"code": ErrorCode.MEAL_ITEM_ACCESS_DENIED, "message": "You do not have access to this meal item"})

    db.delete(db_meal_item)
    db.commit()
    
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
   