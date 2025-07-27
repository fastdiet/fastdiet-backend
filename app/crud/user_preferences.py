from sqlalchemy.orm import Session, selectinload
from app.models import UserPreferences


def get_user_preferences_by_user_id(db: Session, user_id : int ) -> UserPreferences | None:
    return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()

def create_user_preferences(db: Session, user_id: int) -> UserPreferences:
    preferences = UserPreferences(user_id=user_id)
    db.add(preferences)
    db.flush()
    return preferences


def get_user_preferences_details(db: Session, user_id: int) -> UserPreferences | None:
    preferences = (
        db.query(UserPreferences)
        .filter(UserPreferences.user_id == user_id)
        .options(
            selectinload(UserPreferences.diet_type),
            selectinload(UserPreferences.cuisines),
            selectinload(UserPreferences.intolerances)
        )
        .first()
    )

    return preferences


