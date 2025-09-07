import logging
from sqlalchemy.orm import Session
from app.core.errors import ErrorCode
from app.models import User, UserPreferences
from fastapi import HTTPException
from app.crud.diet_type import get_diet_type_by_id
from app.crud.user_preferences import create_user_preferences, get_user_preferences_by_user_id
from app.crud.cuisine_region import get_cuisine_regions_by_ids
from app.crud.intolerance import get_intolerances_by_ids

logger = logging.getLogger(__name__)

# Function to get or create user preferences
def get_or_create_user_preferences(db: Session, user_id: int) -> UserPreferences:
    preferences = get_user_preferences_by_user_id(db, user_id)
    if not preferences:
        logger.info(f"No preferences found for user ID: {user_id}. Creating new default preferences entry.")
        preferences = create_user_preferences(db, user_id)
    return preferences


# Function to calculate the calories using the Mifflin-St Jeor equation
def calculate_calories_goal(user: User, preferences: UserPreferences) -> float:
    if user.gender == "male":
        tmb = (10 * user.weight) + (6.25 * user.height) - (5 * user.age) + 5
    elif user.gender == "female":
        tmb = (10 * user.weight) + (6.25 * user.height) - (5 * user.age) - 161

    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "high": 1.725,
        "very_high": 1.9
    }

    calories = tmb * activity_multipliers[preferences.activity_level]

    if preferences.goal == "lose_weight":
        calories -= 500
    elif preferences.goal == "gain_weight":
        calories += 500

    return max(1200, calories) 

# Function to recalculate calories if all required fields are present
def recalculate_calories_if_possible(db: Session, user: User, preferences: UserPreferences):
    required_fields = [
        user.gender, user.age, user.weight, user.height,
        preferences.activity_level, preferences.goal
    ]

    if all(required_fields):
        logger.info(f"All required fields present for user ID {user.id} ({user.username}). Recalculating calories goal.")
        new_calories = calculate_calories_goal(user, preferences)
        logger.info(f"Calories goal for user ID {user.id} ({user.username}) calculated as: {new_calories}.")
        preferences.calories_goal = new_calories
    else:
        logger.warning(f"Cannot recalculate calories for user ID {user.id} ({user.username}) because some required profile fields are missing.")


# Function to update the diet type of the user preferences
def update_diet(db: Session, user: User, diet_id: int):
    if diet_id is not None:
        diet_type = get_diet_type_by_id(db, diet_id)
        if not diet_type:
            logger.warning(f"User ID {user.id} ({user.username}) failed to update diet type: Diet ID {diet_id} not found.")
            raise HTTPException(
                status_code=404,
                detail={"code": ErrorCode.DIET_TYPE_NOT_FOUND, "message": "Diet type not found"}
            )
    
    preferences = get_or_create_user_preferences(db, user.id)
    preferences.diet_type_id = diet_id

    return preferences

def update_cuisine_preferences(db: Session, user: User, cuisine_ids: list[int]):
    preferences = get_or_create_user_preferences(db, user.id)

    if not cuisine_ids:
        preferences.cuisines = []
        return preferences
    
    
    # Verify all cuisine IDs exist
    existing_cuisines = get_cuisine_regions_by_ids(db, list(set(cuisine_ids)))
    if len(existing_cuisines) != len(set(cuisine_ids)):
        logger.warning(f"User ID {user.id} ({user.username}) failed to update cuisines: One or more provided cuisine IDs are not found.")
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.CUISINE_REGIONS_NOT_FOUND, "message": "Cuisine regions not found"}
        )
    
    preferences.cuisines = existing_cuisines

    return preferences
    

def update_intolerance_preferences(db: Session, user: User, intolerance_ids: list[int]):
    preferences = get_or_create_user_preferences(db, user.id)

    if not intolerance_ids:
        preferences.intolerances = []
        return preferences
    
    existing_intolerances = get_intolerances_by_ids(db, list(set(intolerance_ids)))
    if len(existing_intolerances) != len(set(intolerance_ids)):
        logger.warning(f"User ID {user.id} ({user.username}) failed to update intolerances: One or more provided intolerance IDs are not found.")
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.INTOLERANCES_NOT_FOUND, "message": "Intolerances not found"}
        )
    
    preferences.intolerances = existing_intolerances

    return preferences

def user_has_complex_intolerances(preferences: UserPreferences) -> bool:
    """ Check if the user has intolerances that do not appear as boolean attributes in recipes (gluten_free, dairy_free)"""
    simple_intolerances = {"gluten", "dairy"}
    for intolerance in preferences.intolerances:
        if intolerance.name.lower() not in simple_intolerances:
            return True
    return False

    