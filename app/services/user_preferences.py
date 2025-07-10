from sqlalchemy.orm import Session
from app.models import User, UserPreferences
from fastapi import HTTPException
from app.crud.diet_type import get_diet_type_by_id
from app.crud.user_preferences import create_user_preferences, get_user_preferences_by_user_id
from app.crud.cuisine_region import get_cuisine_regions_by_ids, clear_user_cuisine_preferences, add_cuisine_preference
from app.crud.intolerance import add_intolerance_preference, get_intolerances_by_ids, clear_user_intolerance_preferences


# Function to get or create user preferences
def get_or_create_user_preferences(db: Session, user_id: int) -> UserPreferences:
    preferences = get_user_preferences_by_user_id(db, user_id)
    if not preferences:
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
        preferences.calories_goal = calculate_calories_goal(user, preferences)


# Function to update the diet type of the user preferences
def update_diet(db: Session, user: User, diet_id: int):
    if diet_id is not None:
        diet_type = get_diet_type_by_id(db, diet_id)
        if not diet_type:
            raise HTTPException(status_code=404, detail="Diet type not found")
    
    preferences = get_or_create_user_preferences(db, user.id)
    preferences.diet_type_id = diet_id

    return preferences

def update_cuisine_preferences(db: Session, user: User, cuisine_ids: list[int]):
    preferences = get_or_create_user_preferences(db, user.id)

    unique_cuisine_ids = set(cuisine_ids)
    
    # Verify all cuisine IDs exist
    if unique_cuisine_ids:
        existing_cuisines = get_cuisine_regions_by_ids(db, list(cuisine_ids))
        if len(existing_cuisines) != len(unique_cuisine_ids):
            raise HTTPException(status_code=404, detail="Cuisine regions not found")
    
    clear_user_cuisine_preferences(db, preferences.id)
    
    for cuisine_id in unique_cuisine_ids:
        add_cuisine_preference(db, preferences.id, cuisine_id)

    return preferences
    
    

def update_intolerance_preferences(db: Session, user: User, intolerance_ids: list[int]):
    preferences = get_or_create_user_preferences(db, user.id)
    
    unique_intolerance_ids = set(intolerance_ids)
    if unique_intolerance_ids:
        existing_intolerances = get_intolerances_by_ids(db, list(unique_intolerance_ids))
        if len(existing_intolerances) != len(unique_intolerance_ids):
            raise HTTPException(status_code=404, detail="Intolerances not found")
    
    clear_user_intolerance_preferences(db, preferences.id)
    
    for intolerance_id in unique_intolerance_ids:
        add_intolerance_preference(db, preferences.id, intolerance_id)

    return preferences
    
    