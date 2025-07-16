from sqlalchemy.orm import Session
from app.models import DietType


def get_diet_type_by_id(db: Session, id : int ) -> DietType | None:
    return db.query(DietType).filter(DietType.id == id).first()

def get_diet_type_by_name(db: Session, name: str) -> DietType | None:
    return db.query(DietType).filter(DietType.name.ilike(name.strip())).first()

def get_or_create_diet_type(db: Session, diet_type_name: str) -> DietType | None:
    if not diet_type_name:
        return None
    diet_type = get_diet_type_by_name(db, diet_type_name)
    if not diet_type:
        diet_type = DietType(name=diet_type_name.capitalize())
        db.add(diet_type)
        db.flush()

    return diet_type