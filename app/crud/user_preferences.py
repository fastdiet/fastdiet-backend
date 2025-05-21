from sqlalchemy.orm import Session
from app.models import User, UserPreferences


# Function to get a user by username
def get_user_preferences_by_user_id(db: Session, user_id : int ) -> UserPreferences | None:
    return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()

def create_user_preferences(db: Session, user_id: int) -> UserPreferences:
    preferences = UserPreferences(user_id=user_id)
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    return preferences
