from sqlalchemy.orm import Session
from app.models import User, DietType, UserPreferences
from app.schemas.user import UserRegister


# Function to get a user by username
def get_user_preferences_by_user_id(db: Session, user_id : int ) -> UserPreferences | None:
    return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()

def create_user_preferences(db: Session, user_id: int) -> UserPreferences:
    preferences = UserPreferences(user_id=user_id)
    db.add(preferences)
    return preferences

# Function to get a user by email
def get_user_by_email(db: Session, email: str, ) -> User | None:
    return db.query(User).filter(User.email == email).first()