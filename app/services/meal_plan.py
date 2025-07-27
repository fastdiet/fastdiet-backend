from collections import defaultdict
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.errors import ErrorCode
from app.crud.meal_plan import get_meal_plan_for_response, save_meal_plan_to_db
from app.crud.recipe import get_or_create_spoonacular_recipe, get_recipe_suggestions_from_db
from app.crud.user_preferences import get_user_preferences_by_user_id
from app.models.meal_item import MealItem
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.models.user_preferences import UserPreferences
from app.services.meal_plan_generator import MealPlanConfig, MealPlanGenerator, MealPlanGeneratorError, MealSlot
from app.services.spoonacular import SpoonacularService
from app.services.user_preferences import user_has_complex_intolerances


async def generate_meal_plan_for_user(db: Session, user_id: int):
    preferences = get_user_preferences_by_user_id(db, user_id)
    if not preferences:
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.USER_PREFERENCES_NOT_FOUND, "message": "User preferences not found"}
        )
    if not preferences.calories_goal or preferences.calories_goal <=0:
        preferences.calories_goal = 2000
    
    spoon_service= SpoonacularService()
    generator = MealPlanGenerator(preferences, spoon_service)
    try:
        spoonacular_meal_plan = await generator.generate()
    except MealPlanGeneratorError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.MEAL_PLAN_GENERATION_FAILED, "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": ErrorCode.INTERNAL_SERVER_ERROR, "message": "Could not generate meal plan"}
        )
    
    db_meal_plan = save_meal_plan_to_db(db, user_id, spoonacular_meal_plan)
    return get_meal_plan_for_response(db, db_meal_plan.id)


async def get_meal_replacement_suggestions(db: Session, preferences: UserPreferences, meal_item: MealItem | None, limit: int = 5, slot_override: int | None = None) -> list[Recipe]:
    """Generates a list of recipe suggestions to replace a specific meal item"""

    meal_slot = MealSlot(slot_override) if slot_override is not None else MealSlot(meal_item.slot)
    meal_plan_generator = MealPlanGenerator(preferences, None)
    base_params = meal_plan_generator.base_search_params
    target_calories = meal_plan_generator.calories_targets.get(meal_slot)
    min_calories = target_calories - MealPlanConfig.CALORIE_SEARCH_RANGE
    max_calories=target_calories + MealPlanConfig.CALORIE_SEARCH_RANGE
    recipe_suggestions = {}


    print("\n\n\n\n--- Filtros para búsqueda en BD ---")
    print(f"Meal Slot: {meal_slot}")
    #print(f"Exclude IDs: {{{meal_item.recipe_id}}}")
    print(f"Dieta: {preferences.diet_type_id}")
    print(f"Dieta: {preferences.diet_type_id}")
    print(f"Cocinas: {[c.name for c in preferences.cuisines]}")
    print(f"Cocinas: {preferences.cuisines}")
    print(f"Intolerancias: {[c.name for c in preferences.cuisines]}")
    print(f"Intolerancias: {preferences.intolerances}")
    print(f"Min calorías: {min_calories}")
    print(f"Max calorías: {max_calories}")
    print(f"Limite: {limit}")
    print("--- Fin filtros ---\n\n\n\n\n")
  
    if not user_has_complex_intolerances(preferences):
        
        exclude_ids = {meal_item.recipe_id} if meal_item else {}
        db_suggestions = get_recipe_suggestions_from_db(db, exclude_ids, preferences, min_calories, max_calories, limit, meal_slot)
        print("/n/n/n--- Resultados base de datos ---")
        for recipe in db_suggestions:
            print(f"Receta  {recipe.id} - Título: {recipe.title}")
            recipe_suggestions[recipe.id] = recipe
        print("/n/n/n--- Resultados base de datos ---/n/n/n")


    if len(recipe_suggestions) < limit:
        spoon_recipes_needed = limit - len(recipe_suggestions)
        spoon_service = SpoonacularService()
        api_result = await spoon_service.search_recipes(
            diet=base_params.get("diet"),
            intolerances=base_params.get("intolerances"),
            cuisine=base_params.get("cuisines"),
            type=MealPlanConfig.MEAL_TYPES_SPOONACULAR[meal_slot],
            min_calories=min_calories,
            max_calories=max_calories,
            number=spoon_recipes_needed * 2,
            sort="random"
        )

        if api_result.get("error"):
            print(f"Spoonacular API error for {meal_slot.name}: {api_result['error']}")
            return list(recipe_suggestions.values())[:limit]
        
        for recipe in api_result.get("results", []):
            db_recipe = get_or_create_spoonacular_recipe(db, recipe)
            if db_recipe and db_recipe.id not in recipe_suggestions:
                recipe_suggestions[db_recipe.id] = db_recipe
            db.commit()

    return list(recipe_suggestions.values())[:limit]

def meal_plan_to_response(meal_plan: MealPlan) -> dict:
    days_plans = defaultdict(list)
    for item in meal_plan.meal_items:

        recipe_short = {
            "id": item.recipe.id,
            "spoonacular_id": item.recipe.spoonacular_id,
            "title": item.recipe.title,
            "image_url": item.recipe.image_url,
            "ready_min": item.recipe.ready_min,
            "calories": item.recipe.calories,
            "servings": item.recipe.servings
        }
        slot_meal = {
            "meal_item_id": item.id,
            "slot": item.slot,
            "recipe": recipe_short
        }
        days_plans[item.day].append(slot_meal)

    final_days_response = []
    for day_index in range(7):
        meals_for_day = days_plans.get(day_index, [])
        final_days_response.append({
            "day": day_index,
            "meals": meals_for_day
        })

    return {
        "id": meal_plan.id,
        "days": final_days_response
    }
    
