from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import User, UserPreferences
from app.schemas.user import UserRegister, UserUpdate
from app.schemas.user_preferences import CuisineRegionUpdate, DietTypeUpdate, IntoleranceUpdate
from app.core.security import hash_password
from fastapi import HTTPException
from app.crud.user import create_user, get_user_by_email, get_user_by_username, get_user_by_username_or_email
from app.db.db_connection import get_sync_session
from app.crud.diet_type import get_diet_type_by_id
from app.crud.user_preferences import create_user_preferences, get_user_preferences_by_user_id
from app.crud.cuisine_region import get_cuisine_regions_by_ids, clear_user_cuisine_preferences, add_cuisine_preference
from app.crud.intolerance import add_intolerance_preference, get_intolerances_by_ids, clear_user_intolerance_preferences

# Function to update the diet type of the user preferences
def update_diet(db: Session, user: User, diet_update: DietTypeUpdate) -> UserPreferences:

    diet_type = get_diet_type_by_id(db, diet_update.id)
    if not diet_type:
        raise HTTPException(status_code=404, detail="Diet type not found")
    
    preferences = get_user_preferences_by_user_id(db, user.id)
    
    if not preferences:
        preferences = create_user_preferences(db, user.id)
    
    preferences.diet_type_id = diet_update.id
    
    if diet_type.name == "Gluten Free":
        preferences.gluten_free = True
    elif diet_type.name == "Vegetarian":
        preferences.vegetarian = True
    elif diet_type.name == "Vegan":
        preferences.vegan = True
    elif diet_type.name == "Low FODMAP":
        preferences.low_fodmap = True
    
    db.commit()
    db.refresh(preferences)
    return preferences

def update_cuisine_preferences(db: Session, user: User, cuisine_update: CuisineRegionUpdate) -> UserPreferences:
    preferences = get_user_preferences_by_user_id(db, user.id)
    if not preferences:
        preferences = create_user_preferences(db, user.id)
    
    # Verify all cuisine IDs exist
    if cuisine_update.cuisine_ids:
        existing_cuisines = get_cuisine_regions_by_ids(db, cuisine_update.cuisine_ids)
        found_ids = [cuisine.id for cuisine in existing_cuisines]
        missing_ids = set(cuisine_update.cuisine_ids) - set(found_ids)
        
        if missing_ids:
            raise HTTPException(status_code=404, detail="Cuisine regions not found")
    
    clear_user_cuisine_preferences(db, preferences.id)
    
    for cuisine_id in cuisine_update.cuisine_ids:
        add_cuisine_preference(db, preferences.id, cuisine_id)
    
    db.commit()
    db.refresh(preferences)
    
    return preferences

def update_intolerance_preferences(db: Session, user: User, intolerance_update: IntoleranceUpdate) -> UserPreferences:
    preferences = get_user_preferences_by_user_id(db, user.id)
    if not preferences:
        preferences = create_user_preferences(db, user.id)
    
    # Verify all intolerance IDs exist
    if intolerance_update.intolerance_ids:
        existing_intolerances = get_intolerances_by_ids(db, intolerance_update.intolerance_ids)
        found_ids = [intolerance.id for intolerance in existing_intolerances]
        missing_ids = set(intolerance_update.intolerance_ids) - set(found_ids)
        
        if missing_ids:
            raise HTTPException(status_code=404, detail="Intolerances not found")
    
    clear_user_intolerance_preferences(db, preferences.id)
    
    for intolerance_id in intolerance_update.intolerance_ids:
        add_intolerance_preference(db, preferences.id, intolerance_id)
    
    db.commit()
    db.refresh(preferences)
    
    return preferences