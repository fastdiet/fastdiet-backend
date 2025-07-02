from sqlalchemy.orm import Session, selectinload, joinedload

from app.crud.recipe import get_or_create_recipe
from app.models.meal_item import MealItem
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.models.recipes_nutrient import RecipesNutrient


def save_meal_plan_to_db(db: Session, user_id: int, generated_plan: dict[int, dict[int, dict]]):

    meal_plan = MealPlan(user_id=user_id)
    db.add(meal_plan)
    db.flush()
    for day, meals in generated_plan.items():
        for slot, recipe in meals.items():

            db_recipe = get_or_create_recipe(db, recipe)

            meal_item = MealItem(
                day=day,
                slot=slot,
                recipe_id=db_recipe.id,
                meal_plan_id= meal_plan.id
            )
            db.add(meal_item)

    db.commit()
    db.refresh(meal_plan)

    return meal_plan

def get_latest_meal_plan_for_user(db: Session, user_id: int) -> MealPlan | None:
    return (
        db.query(MealPlan)
        .filter(MealPlan.user_id == user_id)
        .options(
            selectinload(MealPlan.meal_items)
            .selectinload(MealItem.recipe)
            .selectinload(Recipe.recipes_nutrients)
            .joinedload(RecipesNutrient.nutrient)
        )
        .order_by(MealPlan.created_at.desc())
        .first()
    )