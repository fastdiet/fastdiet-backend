from sqlalchemy.orm import Session

from app.models.nutrient import Nutrient


def get_or_create_nutrient(db: Session, nutrient_name: str, is_primary: bool = False) -> Nutrient:
    nutrient = db.query(Nutrient).filter(Nutrient.name.ilike(nutrient_name.strip())).first()
    if not nutrient:
        nutrient = Nutrient(name=nutrient_name.capitalize(), is_primary=is_primary)
        db.add(nutrient)
    elif is_primary and not nutrient.is_primary:
        nutrient.is_primary = True
        db.add(nutrient)
    db.flush()
    return nutrient