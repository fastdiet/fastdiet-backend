from sqlalchemy.orm import Session
from app.models.dish_type import DishType


def get_dish_type_by_id(db: Session, id : int ) -> DishType | None:
    return db.query(DishType).filter(DishType.id == id).first()

def get_dish_type_by_name(db: Session, name: str) -> DishType | None:
    normalized_name = name.strip().lower()
    return db.query(DishType).filter(DishType.name == normalized_name).first()

def get_or_create_dish_type(db: Session, dish_type_name: str) -> DishType | None:
    if not dish_type_name:
        return None
    normalized_name = dish_type_name.strip().lower()
    dish_type = get_dish_type_by_name(db, dish_type_name)
    if not dish_type:
        dish_type = DishType(name=normalized_name)
        db.add(dish_type)
        db.flush()
    return dish_type