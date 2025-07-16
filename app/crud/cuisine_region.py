from sqlalchemy.orm import Session
from app.models import CuisineRegion, UserPreferencesCuisine
from app.crud.user_preferences import get_user_preferences_by_user_id


def get_cuisine_regions_by_ids(db: Session, cuisine_ids: list[int] ) ->  list[CuisineRegion]:
    return db.query(CuisineRegion).filter(CuisineRegion.id.in_(cuisine_ids)).all()

def get_cuisine_region_by_id(db: Session, cuisine_id: int) -> CuisineRegion | None:
    return db.query(CuisineRegion).filter(CuisineRegion.id == cuisine_id).first()


def get_cuisine_region_by_name(db: Session, cuisine_name: str) -> CuisineRegion | None:
    return db.query(CuisineRegion).filter(CuisineRegion.name.ilike(cuisine_name.strip())).first()

def get_or_create_cuisine_region(db: Session, cuisine_name: str) -> CuisineRegion | None:
    if not cuisine_name:
        return None
    cuisine = get_cuisine_region_by_name(db, cuisine_name)
    if not cuisine:
        cuisine = CuisineRegion(name=cuisine_name.capitalize())
        db.add(cuisine)
        db.flush()
    return cuisine

def get_user_cuisine_preferences(db: Session, user_id: int) -> list[UserPreferencesCuisine]:
    preferences = get_user_preferences_by_user_id(db, user_id)
    if not preferences:
        return []
    
    return db.query(UserPreferencesCuisine).filter(
        UserPreferencesCuisine.preference_id == preferences.id
    ).all()


def add_cuisine_preference(db: Session, preference_id: int, cuisine_id: int) -> UserPreferencesCuisine:
    cuisine_preference = UserPreferencesCuisine(
        preference_id=preference_id,
        cuisine_id=cuisine_id
    )
    db.add(cuisine_preference)
    return cuisine_preference

def clear_user_cuisine_preferences(db: Session, preference_id: int) -> None:
    db.query(UserPreferencesCuisine).filter(
        UserPreferencesCuisine.preference_id == preference_id
    ).delete()