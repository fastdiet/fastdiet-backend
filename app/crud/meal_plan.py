from sqlalchemy.orm import Session, selectinload
from app.core.meal_plan_config import MealSlot
from app.models.meal_item import MealItem
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.models.recipes_ingredient import RecipesIngredient



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
    meal_plan = MealPlan(user_id=user_id)
    db.add(meal_plan)
    db.flush()

    meal_items = []

    slot_to_meal_type = {
        MealSlot.BREAKFAST.value: "breakfast",
        MealSlot.LUNCH.value: "lunch",
        MealSlot.DINNER.value: "dinner",
    }

    for day, meals in generated_plan.items():
        for slot, recipe_data in meals.items():
            meal_items.append(MealItem(
                day=day,
                slot=slot,
                recipe_id=recipe_data.id,
                meal_plan_id=meal_plan.id,
                meal_type=slot_to_meal_type[slot]
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

def get_latest_meal_plan_for_shopping_list(db: Session, user_id: int) -> MealPlan | None:
     return (
        db.query(MealPlan)
        .filter(MealPlan.user_id == user_id)
        .options(
            selectinload(MealPlan.meal_items)
            .selectinload(MealItem.recipe)
            .selectinload(Recipe.recipes_ingredients)
            .selectinload(RecipesIngredient.ingredient)
        )
        .order_by(MealPlan.created_at.desc())
        .first()
    )