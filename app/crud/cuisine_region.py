from sqlalchemy.orm import Session
from app.models import CuisineRegion


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


