from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.db_connection import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.user_preferences import recalculate_calories_if_possible, update_activity, update_cuisine_preferences, update_diet, update_goal_preference, update_intolerance_preferences
from app.schemas.user_preferences import ActivityUpddate, CuisineRegionUpdate, GoalUpdate, IntoleranceUpdate, UserPreferencesResponse, DietTypeUpdate


router = APIRouter(tags=["users_preferences"], prefix="/user_preferences")


@router.patch("/goal", response_model=UserPreferencesResponse)
def update_goal(
    goal_update: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's goal"""
    preferences = update_goal_preference(db, current_user, goal_update.goal)
    preferences = recalculate_calories_if_possible(db, current_user, preferences)
    
    return preferences

@router.patch("/activity-level", response_model=UserPreferencesResponse)
def update_activity_level(
    activity_update: ActivityUpddate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's activity level"""
    preferences = update_activity(db, current_user, activity_update.activity_level)
    return recalculate_calories_if_possible(db, current_user, preferences)

@router.patch("/diet-type", response_model=UserPreferencesResponse)
def update_diet_type(
    diet_update: DietTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's diet type preference"""
    return update_diet(db, current_user, diet_update.id)

@router.patch("/cuisine-types", response_model=UserPreferencesResponse)
def update_cuisine_types(
    cuisine_update: CuisineRegionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's cuisine type preferences"""
    return update_cuisine_preferences(db, current_user, cuisine_update.cuisine_ids)

@router.patch("/intolerances", response_model=UserPreferencesResponse)
def update_intolerances(
    intolerance_update: IntoleranceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's intoleraces"""
    return update_intolerance_preferences(db, current_user, intolerance_update.intolerance_ids)