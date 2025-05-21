from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.db_connection import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.meal_plan import MealPlanResponse
from app.services.user_preferences import recalculate_calories_if_possible, update_activity, update_cuisine_preferences, update_diet, update_goal_preference, update_intolerance_preferences
from app.schemas.user_preferences import ActivityUpddate, CuisineRegionUpdate, GoalUpdate, IntoleranceUpdate, UserPreferencesResponse, DietTypeUpdate


router = APIRouter(tags=["meal_plans"], prefix="/meal_plans")


@router.post("/generate", response_model=MealPlanResponse)
async def generate_meal_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to generate a meal plan for the user"""
    meal_plan = generate_meal_plan_for_user(db, current_user.id)
    return meal_plan
    