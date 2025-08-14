import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.db_connection import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.user_preferences import get_or_create_user_preferences, recalculate_calories_if_possible, update_cuisine_preferences, update_diet, update_intolerance_preferences
from app.schemas.user_preferences import ActivityUpdateResponse, ActivityUpddate, CuisineRegionUpdate, CuisinesUpdateResponse, DietTypeUpdateResponse, GoalUpdate, GoalUpdateResponse, IntoleranceUpdate, IntolerancesUpdateResponse, DietTypeUpdate


logger = logging.getLogger(__name__)

router = APIRouter(tags=["users_preferences"], prefix="/user_preferences")

@router.patch("/goal", response_model=GoalUpdateResponse)
def update_goal(
    goal_update: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's goal"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is updating their goal to '{goal_update.goal}'.")
    preferences = get_or_create_user_preferences(db, current_user.id)

    preferences.goal = goal_update.goal
    recalculate_calories_if_possible(db, current_user, preferences)

    db.commit()
    db.refresh(preferences)

    logger.info(f"Goal for user ID: {current_user.id} ({current_user.username}) updated. New goal: {preferences.goal}")

    return GoalUpdateResponse(
        goal=preferences.goal,
        calories_goal=preferences.calories_goal
    )
    

@router.patch("/activity-level", response_model=ActivityUpdateResponse)
def update_activity_level(
    activity_update: ActivityUpddate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's activity level"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is updating activity level to '{activity_update.activity_level}'.")
    preferences = get_or_create_user_preferences(db, current_user.id)
    
    preferences.activity_level = activity_update.activity_level
    recalculate_calories_if_possible(db, current_user, preferences)

    db.commit()
    db.refresh(preferences)

    logger.info(f"Activity level for user ID: {current_user.id} ({current_user.username}) updated. New activity level: {preferences.activity_level}")

    return ActivityUpdateResponse(
        activity_level=preferences.activity_level,
        calories_goal=preferences.calories_goal
    )

@router.patch("/diet-type", response_model=DietTypeUpdateResponse)
def update_diet_type(
    diet_update: DietTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's diet type preference"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is updating diet type preference to ID: {diet_update.id}.")
    preferences = update_diet(db, current_user, diet_update.id)
    db.commit()
    db.refresh(preferences)
    db.refresh(preferences, attribute_names=['diet_type'])
    
    logger.info(f"Diet type for user ID: {current_user.id} ({current_user.username}) updated. New diet type: {preferences.diet_type.name}")
    return DietTypeUpdateResponse(diet_type=preferences.diet_type)

@router.patch("/cuisine-types", response_model=CuisinesUpdateResponse)
def update_cuisine_types(
    cuisine_update: CuisineRegionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's cuisine type preferences"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is updating cuisine preferences.")
    preferences = update_cuisine_preferences(db, current_user, cuisine_update.cuisine_ids)
    db.commit()
    db.refresh(preferences)
    
    logger.info(f"Cuisine types for user ID: {current_user.id} ({current_user.username}) updated successfully.")

    return CuisinesUpdateResponse(cuisines=[cuisine for cuisine in preferences.cuisines])

@router.patch("/intolerances", response_model=IntolerancesUpdateResponse)
def update_intolerances(
    intolerance_update: IntoleranceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's intoleraces"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is updating intolerance preferences.")
    preferences = update_intolerance_preferences(db, current_user, intolerance_update.intolerance_ids)
    db.commit()
    db.refresh(preferences)
    
    logger.info(f"Intolerances for user ID: {current_user.id} ({current_user.username}) updated successfully.")
    return IntolerancesUpdateResponse(intolerances=[intolerance for intolerance in preferences.intolerances])