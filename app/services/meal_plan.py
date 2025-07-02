from collections import defaultdict
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.crud.meal_plan import save_meal_plan_to_db
from app.crud.user_preferences import get_user_preferences_by_user_id
from app.models.meal_plan import MealPlan
from app.services.meal_plan_generator import MealPlanGenerator, MealPlanGeneratorError
from app.services.spoonacular import SpoonacularService


async def generate_meal_plan_for_user(db: Session, user_id: int):
    preferences = get_user_preferences_by_user_id(db, user_id)
    if not preferences:
        raise HTTPException(status_code=404, detail="User preferences not found")
    if not preferences.calories_goal or preferences.calories_goal <=0:
        preferences.calories_goal = 2000
    
    spoon_service= SpoonacularService()
    generator = MealPlanGenerator(preferences, spoon_service)
    try:
        spoonacular_meal_plan = await generator.generate()
    except MealPlanGeneratorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not generate meal plan")
    
    return save_meal_plan_to_db(db, user_id, spoonacular_meal_plan)

def meal_plan_to_response(meal_plan: MealPlan) -> dict:
    days_plans = defaultdict(list)
    for item in meal_plan.meal_items:

        recipe_short = {
            "id": item.recipe.id,
            "spoonacular_id": item.recipe.spoonacular_id,
            "title": item.recipe.title,
            "image_url": item.recipe.image_url,
            "ready_min": item.recipe.ready_min,
            "calories": item.recipe.calories
        }
        slot_meal = {
            "slot": item.slot,
            "recipe": recipe_short
        }
        days_plans[item.day].append(slot_meal)

    return {
        "id": meal_plan.id,
        "days": [
            {"day": day_idx, "meals": meals}
            for day_idx, meals in sorted(days_plans.items())
        ]
    }
    
