from sqlalchemy.orm import Session
from app.models import User, UserPreferences
from fastapi import HTTPException
from app.crud.diet_type import get_diet_type_by_id
from app.crud.user_preferences import create_user_preferences, get_user_preferences_by_user_id
from app.crud.cuisine_region import get_cuisine_regions_by_ids, clear_user_cuisine_preferences, add_cuisine_preference
from app.crud.intolerance import add_intolerance_preference, get_intolerances_by_ids, clear_user_intolerance_preferences
import spoonacular
# Function to get or create user preferences
def get_or_create_user_preferences(db: Session, user_id: int) -> UserPreferences:
    preferences = get_user_preferences_by_user_id(db, user_id)
    if not preferences:
        preferences = create_user_preferences(db, user_id)
    return preferences

# Function to update the goal of the user preferences
def generate_meal_plan_for_user(db: Session, user_id: int) -> MealPlan:
    preferences = get_user_preferences_by_user_id(db, user_id)
    if not preferences:
        raise HTTPException(status_code=404, detail="User preferences not found")
    

    
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
def recalculate_calories_if_possible(db: Session, user: User, preferences: UserPreferences) -> UserPreferences:
    required_fields = [
        user.gender, user.age, user.weight, user.height,
        preferences.activity_level, preferences.goal
    ]

    if all(required_fields):
        preferences.calories_goal = calculate_calories_goal(user, preferences)
        db.commit()
        db.refresh(preferences)

    return preferences


# Function to update the activity level of the user preferences
def update_activity(db: Session, user: User, activity_level: str) -> UserPreferences:
    preferences = get_or_create_user_preferences(db, user.id)
    preferences.activity_level = activity_level
    db.commit()
    db.refresh(preferences)

    return preferences

# Function to update the diet type of the user preferences
def update_diet(db: Session, user: User, diet_id: int) -> UserPreferences:

    diet_type = get_diet_type_by_id(db, diet_id)
    if not diet_type:
        raise HTTPException(status_code=404, detail="Diet type not found")
    
    preferences = get_or_create_user_preferences(db, user.id)
    preferences.diet_type_id = diet_id
    
    db.commit()
    db.refresh(preferences)
    return preferences

def update_cuisine_preferences(db: Session, user: User, cuisine_ids: list[int]) -> UserPreferences:
    preferences = get_or_create_user_preferences(db, user.id)
    
    # Verify all cuisine IDs exist
    if cuisine_ids:
        existing_cuisines = get_cuisine_regions_by_ids(db, cuisine_ids)
        found_ids = [cuisine.id for cuisine in existing_cuisines]
        missing_ids = set(cuisine_ids) - set(found_ids)
        
        if missing_ids:
            raise HTTPException(status_code=404, detail="Cuisine regions not found")
    
    clear_user_cuisine_preferences(db, preferences.id)
    
    for cuisine_id in cuisine_ids:
        add_cuisine_preference(db, preferences.id, cuisine_id)
    
    db.commit()
    db.refresh(preferences)
    
    return preferences

def update_intolerance_preferences(db: Session, user: User, intolerance_ids: list[int]) -> UserPreferences:
    preferences = get_or_create_user_preferences(db, user.id)
    
    # Verify all intolerance IDs exist
    if intolerance_ids:
        existing_intolerances = get_intolerances_by_ids(db, intolerance_ids)
        found_ids = [intolerance.id for intolerance in existing_intolerances]
        missing_ids = set(intolerance_ids) - set(found_ids)
        
        if missing_ids:
            raise HTTPException(status_code=404, detail="Intolerances not found")
    
    clear_user_intolerance_preferences(db, preferences.id)
    
    for intolerance_id in intolerance_ids:
        add_intolerance_preference(db, preferences.id, intolerance_id)
    
    db.commit()
    db.refresh(preferences)
    
    return preferences