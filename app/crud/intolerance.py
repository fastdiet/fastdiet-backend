from sqlalchemy.orm import Session
from app.models import Intolerance, UserPreferencesIntolerance
from app.crud.user_preferences import get_user_preferences_by_user_id


# Function to get multiple intolerances by their IDs
def get_intolerances_by_ids(db: Session, intolerance_ids: list[int] ) ->  list[Intolerance]:
    return db.query(Intolerance).filter(Intolerance.id.in_(intolerance_ids)).all()

# Function to get an intolerance by its ID
def get_intolerance_by_id(db: Session, intolerance_id: int) -> Intolerance | None:
    return db.query(Intolerance).filter(Intolerance.id == intolerance_id).first()

# Function to get all intolerance preferences for a user
def get_user_intolerance_preferences(db: Session, user_id: int) -> list[UserPreferencesIntolerance]:
    preferences = get_user_preferences_by_user_id(db, user_id)
    if not preferences:
        return []
    
    return db.query(UserPreferencesIntolerance).filter(
        UserPreferencesIntolerance.preference_id == preferences.id
    ).all()

# Function to add an intolerance preference for a user
def add_intolerance_preference(db: Session, preference_id: int, intolerance_id: int) -> UserPreferencesIntolerance:
    intolerance_preference = UserPreferencesIntolerance(
        preference_id=preference_id,
        intolerance_id=intolerance_id
    )
    db.add(intolerance_preference)
    return intolerance_preference

# Function to remove all intolerance preferences for a user
def clear_user_intolerance_preferences(db: Session, preference_id: int) -> None:
    db.query(UserPreferencesIntolerance).filter(
        UserPreferencesIntolerance.preference_id == preference_id
    ).delete()