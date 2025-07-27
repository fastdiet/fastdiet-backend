from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.db_connection import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.user_preferences import get_or_create_user_preferences, recalculate_calories_if_possible, update_cuisine_preferences, update_diet, update_intolerance_preferences
from app.schemas.user_preferences import ActivityUpdateResponse, ActivityUpddate, CuisineRegionUpdate, CuisinesUpdateResponse, DietTypeUpdateResponse, GoalUpdate, GoalUpdateResponse, IntoleranceUpdate, IntolerancesUpdateResponse, DietTypeUpdate


router = APIRouter(tags=["users_preferences"], prefix="/user_preferences")


@router.patch("/goal", response_model=GoalUpdateResponse)
def update_goal(
    goal_update: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's goal"""
    preferences = get_or_create_user_preferences(db, current_user.id)

    preferences.goal = goal_update.goal
    recalculate_calories_if_possible(db, current_user, preferences)

    db.commit()
    db.refresh(preferences)

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
    preferences = get_or_create_user_preferences(db, current_user.id)
    
    preferences.activity_level = activity_update.activity_level
    recalculate_calories_if_possible(db, current_user, preferences)

    db.commit()
    db.refresh(preferences)

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
    preferences = update_diet(db, current_user, diet_update.id)
    db.commit()
    db.refresh(preferences)
    db.refresh(preferences, attribute_names=['diet_type'])
    
    return DietTypeUpdateResponse(diet_type=preferences.diet_type)

@router.patch("/cuisine-types", response_model=CuisinesUpdateResponse)
def update_cuisine_types(
    cuisine_update: CuisineRegionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's cuisine type preferences"""
    preferences = update_cuisine_preferences(db, current_user, cuisine_update.cuisine_ids)
    db.commit()
    db.refresh(preferences)
    
    return CuisinesUpdateResponse(cuisines=[cuisine for cuisine in preferences.cuisines])

@router.patch("/intolerances", response_model=IntolerancesUpdateResponse)
def update_intolerances(
    intolerance_update: IntoleranceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's intoleraces"""
    preferences = update_intolerance_preferences(db, current_user, intolerance_update.intolerance_ids)
    db.commit()
    db.refresh(preferences)
    
    
    return IntolerancesUpdateResponse(intolerances=[intolerance for intolerance in preferences.intolerances])