from sqlalchemy.orm import Session, selectinload
from app.crud.recipe import get_or_create_spoonacular_recipe
from app.models.meal_item import MealItem
from app.models.meal_plan import MealPlan



def get_meal_plan_for_response(db: Session, meal_plan_id: int) -> MealPlan | None:
 
    return (
        db.query(MealPlan)
        .filter(MealPlan.id == meal_plan_id)
        .options(selectinload(MealPlan.meal_items).selectinload(MealItem.recipe))
        .first()
    )

def get_meal_plan_by_id(db: Session, meal_plan_id: int) -> MealPlan | None:
    return (
        db.query(MealPlan)
        .filter(MealPlan.id == meal_plan_id)
        .first()
    )


def save_meal_plan_to_db(db: Session, user_id: int, generated_plan: dict[int, dict[int, dict]]):

    recipe_map = {}
    for day, meals in generated_plan.items():
        for slot, recipe_data in meals.items():
            spoon_id = recipe_data.get("id")
            if spoon_id not in recipe_map:
                recipe_map[spoon_id] = get_or_create_spoonacular_recipe(db, recipe_data)


    meal_plan = MealPlan(user_id=user_id)
    db.add(meal_plan)
    db.flush()

    meal_items = []
    for day, meals in generated_plan.items():
        for slot, recipe_data in meals.items():
            db_recipe = recipe_map[recipe_data["id"]]
            meal_items.append(MealItem(
                day=day,
                slot=slot,
                recipe_id=db_recipe.id,
                meal_plan_id=meal_plan.id
            ))
    
    db.add_all(meal_items)
    db.commit()

    return meal_plan

def get_latest_meal_plan_for_user(db: Session, user_id: int) -> MealPlan | None:
    return (
        db.query(MealPlan)
        .filter(MealPlan.user_id == user_id)
        .options(selectinload(MealPlan.meal_items).selectinload(MealItem.recipe))
        .order_by(MealPlan.created_at.desc())
        .first()
    )
