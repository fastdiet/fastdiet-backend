from collections import defaultdict
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.errors import ErrorCode
from app.core.meal_plan_config import MEAL_TYPE_SUGGESTION_CONFIG, MealPlanGeneratorError
from app.crud.diet_type import get_or_create_diet_type
from app.crud.meal_plan import get_meal_plan_for_response, save_meal_plan_to_db
from app.crud.recipe import get_or_create_spoonacular_recipe, get_recipe_suggestions_from_db
from app.crud.user_preferences import get_user_preferences_by_user_id
from app.models.meal_item import MealItem
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.models.user_preferences import UserPreferences
from app.services.meal_plan_generator import MealPlanGenerator
from app.services.spoonacular import SpoonacularService
from app.services.user_preferences import user_has_complex_intolerances


logger = logging.getLogger(__name__)

async def generate_meal_plan_for_user(db: Session, user_id: int):
    preferences = get_user_preferences_by_user_id(db, user_id)
    if not preferences:
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.USER_PREFERENCES_NOT_FOUND, "message": "User preferences not found"}
        )
    if not preferences.calories_goal or preferences.calories_goal <=0:
        logger.warning(f"User ID {user_id} has no calorie goal. Defaulting to 2000 kcal for generation.")
        preferences.calories_goal = 2000
    
    spoon_service= SpoonacularService()
    generator = MealPlanGenerator(preferences, db, spoon_service)
    try:
        plan_structure, status = await generator.generate()
    except MealPlanGeneratorError as e:
        logger.warning(f"Meal plan generation failed for user ID {user_id} with a generator error: {e}")
        raise HTTPException(
            status_code=400,
            detail={"code": e.code, "message": str(e)}
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred generating meal plan for user ID {user_id}.", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"code": ErrorCode.INTERNAL_SERVER_ERROR, "message": "Could not generate meal plan"}
        )
    
    db_meal_plan = save_meal_plan_to_db(db, user_id, plan_structure)
    return get_meal_plan_for_response(db, db_meal_plan.id), status


async def fetch_spoon_recipes(
    db: Session,
    preferences: UserPreferences,
    spoonacular_type_to_search: str,
    limit: int,
    offset: int = 0,
) -> list[Recipe]:
    """Fetch recipes from Spoonacular with diet & intolerances and persist them."""

    spoon = SpoonacularService()
    generator = MealPlanGenerator(preferences, db, None)
    base_params = generator.base_search_params

    diet_used = base_params.get("diet")

    api_result = await spoon.search_recipes(
        diet=diet_used,
        intolerances=base_params.get("intolerances"),
        cuisine=base_params.get("cuisines"),
        type=spoonacular_type_to_search,
        min_calories=None, 
        max_calories=None,
        number=limit,
        offset=offset,
        sort="random"
    )

    if api_result.get("error"):
        logger.warning(f"Spoonacular error in suggestions: {api_result['error']}")
        return []

    recipes: list[Recipe] = []
    added_ids = set()

    for recipe in api_result.get("results", []):
        db_recipe, _ = get_or_create_spoonacular_recipe(db, recipe)

        if not db_recipe:
            continue

        if diet_used:
            is_associated = any(
                dt.name.lower() == diet_used.lower()
                for dt in db_recipe.diet_types
            )
            if not is_associated:
                diet_obj = get_or_create_diet_type(db, diet_used)
                if diet_obj:
                    db_recipe.diet_types.append(diet_obj)

        if db_recipe.id not in added_ids:
            recipes.append(db_recipe)
            added_ids.add(db_recipe.id)


        if len(recipes) >= limit:
            break
    
    db.commit() 
    logger.info(f"[Spoonacular] offset={offset} -> {len(recipes)} recipes stored")

    return recipes


async def get_meal_replacement_suggestions(
        db: Session, preferences: UserPreferences,
        meal_item: MealItem | None, meal_type: str,
        limit: int = 5, offset: int = 0
    ) -> list[Recipe]:
    """Generates a list of recipe suggestions to replace a specific meal item"""

    config = MEAL_TYPE_SUGGESTION_CONFIG.get(meal_type, MEAL_TYPE_SUGGESTION_CONFIG["snack"])
    db_dish_types_to_search = config["db_dish_types"]
    spoonacular_type_to_search = config["spoonacular_type"]
    
    recipe_suggestions = {}

    logger.debug(f"Searching suggestions for user {preferences.user_id}. Meal type: {meal_type}, Diet ID: {preferences.diet_type_id}")
  
    if not user_has_complex_intolerances(preferences):
        
        exclude_ids = {meal_item.recipe_id} if meal_item else {}
        db_suggestions = get_recipe_suggestions_from_db(
            db, exclude_ids, preferences, db_dish_types_to_search, limit, None, None, offset
        )
        for recipe in db_suggestions:
            recipe_suggestions[recipe.id] = recipe
        logger.info(f"[DB] offset={offset} -> {len(db_suggestions)} recetas")

        # ✅ Si no hay suficientes pero solo en la primera página → completamos con API
        if offset == 0 and len(recipe_suggestions) < limit:
            spoon_needed = limit - len(recipe_suggestions)
            logger.info(f"Not enough DB suggestions.. Fetching {spoon_needed} from Spoonacular")
            spoon_results = await fetch_spoon_recipes(
                db, preferences, spoonacular_type_to_search, spoon_needed
            )
            for r in spoon_results:
                if r.id not in exclude_ids:
                    recipe_suggestions[r.id] = r

    else:
        logger.info("User has complex intolerances. Fetching all suggestions from Spoonacular API.")

        spoon_results = await fetch_spoon_recipes(
            db, preferences, spoonacular_type_to_search, limit, offset
        )

        for r in spoon_results:
            if r.id not in exclude_ids:
                recipe_suggestions[r.id] = r

    return list(recipe_suggestions.values())[:limit]

def meal_plan_to_response(meal_plan: MealPlan, lang: str) -> dict:

    items_by_day = defaultdict(list)
    for item in meal_plan.meal_items:
        items_by_day[item.day].append(item)

    final_days_response = []
    for day_index in range(7):
        base_slots = {
            0: {"meal_item_id": None, "slot": 0, "meal_type": "breakfast", "recipe": None},
            1: {"meal_item_id": None, "slot": 1, "meal_type": "lunch", "recipe": None},
            2: {"meal_item_id": None, "slot": 2, "meal_type": "dinner", "recipe": None},
        }
        extra_meals = []
        
        for item in items_by_day.get(day_index, []):
            recipe_short = {
                "id": item.recipe.id,
                "spoonacular_id": item.recipe.spoonacular_id,
                "title": item.recipe.title if lang != "es" else item.recipe.title_es,
                "image_url": item.recipe.image_url,
                "ready_min": item.recipe.ready_min,
                "calories": item.recipe.calories,
                "servings": item.recipe.servings
            }
            slot_meal = {
                "meal_item_id": item.id,
                "slot": item.slot,
                "meal_type": item.meal_type,
                "recipe": recipe_short
            }

            if item.slot in base_slots:
                base_slots[item.slot] = slot_meal
            else:
                extra_meals.append(slot_meal)

        extra_meals.sort(key=lambda x: x['slot'])
        
        final_meals_for_day = list(base_slots.values()) + extra_meals
        
        final_days_response.append({
            "day": day_index,
            "meals": final_meals_for_day
        })

    return {
        "id": meal_plan.id,
        "days": final_days_response,
    }
    
