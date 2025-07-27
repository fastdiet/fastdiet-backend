from sqlalchemy.orm import Session, joinedload

from app.models.meal_item import MealItem

def get_complete_meal_item_by_id(db: Session, id: int) -> MealItem | None:
    return db.query(MealItem).options(
        joinedload(MealItem.recipe), 
        joinedload(MealItem.meal_plan)
    ).filter(MealItem.id == id).first()

def get_meal_item_by_id(db: Session, id: int) -> MealItem | None:
    return db.query(MealItem).options(
        joinedload(MealItem.meal_plan)
    ).filter(MealItem.id == id).first()


def create_db_meal_item(db: Session, meal_plan_id: int, recipe_id: int, day_index: int, slot: int) -> MealItem | None:
    new_meal_item = MealItem(
        recipe_id= recipe_id,
        meal_plan_id = meal_plan_id,
        day = day_index,
        slot = slot
    )
    db.add(new_meal_item)
    db.commit()
    db.refresh(new_meal_item)
    return new_meal_item



