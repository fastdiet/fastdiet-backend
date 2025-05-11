from sqlalchemy.orm import Session
from app.models import CuisineRegion, UserPreferencesCuisine
from app.crud.user_preferences import get_user_preferences_by_user_id


# Function to get multiple cuisine regions by their IDs
def get_cuisine_regions_by_ids(db: Session, cuisine_ids: list[int] ) ->  list[CuisineRegion]:
    return db.query(CuisineRegion).filter(CuisineRegion.id.in_(cuisine_ids)).all()

# Function to get a cuisine region by its ID
def get_cuisine_region_by_id(db: Session, cuisine_id: int) -> CuisineRegion | None:
    return db.query(CuisineRegion).filter(CuisineRegion.id == cuisine_id).first()

# Function to get all cuisine preferences for a user
def get_user_cuisine_preferences(db: Session, user_id: int) -> list[UserPreferencesCuisine]:
    preferences = get_user_preferences_by_user_id(db, user_id)
    if not preferences:
        return []
    
    return db.query(UserPreferencesCuisine).filter(
        UserPreferencesCuisine.preference_id == preferences.id
    ).all()

# Function to add a cuisine preference for a user
def add_cuisine_preference(db: Session, preference_id: int, cuisine_id: int) -> UserPreferencesCuisine:
    cuisine_preference = UserPreferencesCuisine(
        preference_id=preference_id,
        cuisine_id=cuisine_id
    )
    db.add(cuisine_preference)
    return cuisine_preference

# Function to remove all cuisine preferences for a user
def clear_user_cuisine_preferences(db: Session, preference_id: int) -> None:
    db.query(UserPreferencesCuisine).filter(
        UserPreferencesCuisine.preference_id == preference_id
    ).delete()