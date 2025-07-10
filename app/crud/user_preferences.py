from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload, joinedload
from app.models import User, UserPreferences
from app.models.user_preferences_cuisine import UserPreferencesCuisine
from app.models.user_preferences_intolerance import UserPreferencesIntolerance
from app.schemas.user_preferences import UserPreferencesResponse


# Function to get a user by username
def get_user_preferences_by_user_id(db: Session, user_id : int ) -> UserPreferences | None:
    return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()

def create_user_preferences(db: Session, user_id: int) -> UserPreferences:
    preferences = UserPreferences(user_id=user_id)
    db.add(preferences)
    db.flush()
    return preferences

def user_preferences_to_response(preferences: UserPreferences) -> UserPreferencesResponse:
    return UserPreferencesResponse(
        id=preferences.id,
        user_id=preferences.user_id,
        diet=preferences.diet_type,
        cuisines=[pref_cuisine.cuisine for pref_cuisine in preferences.user_preferences_cuisines],
        intolerances=[pref_intolerance.intolerance for pref_intolerance in preferences.user_preferences_intolerances],
        activity_level=preferences.activity_level,
        goal=preferences.goal,
        max_ready_min=preferences.max_ready_min,
        servings=preferences.servings,
        calories_goal=preferences.calories_goal,
        sustainable=preferences.sustainable,
    )


def get_user_preferences_details(db: Session, user_id: int) -> UserPreferencesResponse | None:
    preferences = (
        db.query(UserPreferences)
        .filter(UserPreferences.user_id == user_id)
        .options(
            selectinload(UserPreferences.diet_type),
            selectinload(UserPreferences.user_preferences_cuisines).joinedload(UserPreferencesCuisine.cuisine),
            selectinload(UserPreferences.user_preferences_intolerances).joinedload(UserPreferencesIntolerance.intolerance)
        )
        .first()
    )

    if not preferences:
        return None

    return UserPreferencesResponse(
        id=preferences.id,
        user_id=preferences.user_id,
        diet=preferences.diet_type if preferences.diet_type else None,
        cuisines=[pref_cuisine.cuisine for pref_cuisine in preferences.user_preferences_cuisines],
        intolerances=[pref_intolerance.intolerance for pref_intolerance in preferences.user_preferences_intolerances],
        activity_level=preferences.activity_level,
        goal=preferences.goal,
        max_ready_min=preferences.max_ready_min,
        servings=preferences.servings,
        calories_goal=preferences.calories_goal,
        sustainable=preferences.sustainable,
    )


