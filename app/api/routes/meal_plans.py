from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.crud.meal_plan import get_latest_meal_plan_for_user
from app.db.db_connection import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.meal_plan import MealPlanResponse
from app.services.meal_plan import generate_meal_plan_for_user, meal_plan_to_response
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
        raise HTTPException(status_code=404, detail="No meal plan found for this user")
    return meal_plan_to_response(meal_plan)

@router.get("/recipe", response_model=dict)
async def get_random_recipe(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    spoonacular = SpoonacularService()
    recipes = await spoonacular.search_recipes(
        cuisine="",
        type="",
        diet="pescatarian",
        intolerances="Sesame, Grain",
        sort="",
        number=1
    )

    return recipes
   