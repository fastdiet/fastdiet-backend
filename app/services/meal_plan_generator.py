import logging
import random
from app.core.errors import ErrorCode
from app.core.meal_plan_config import MEAL_TYPE_SUGGESTION_CONFIG, MealPlanConfig, MealPlanGeneratorError, MealSlot, PlanGenerationStatus
from app.crud.diet_type import get_or_create_diet_type
from app.crud.recipe import get_or_create_spoonacular_recipe, get_recipe_suggestions_from_db
from app.models.recipe import Recipe
from app.models.user_preferences import UserPreferences
from app.services.spoonacular import SpoonacularService
from sqlalchemy.orm import Session

from app.services.user_preferences import user_has_complex_intolerances


logger = logging.getLogger(__name__)    

class MealPlanGenerator:
    def __init__(self, preferences: UserPreferences, db: Session, spoon_service: SpoonacularService):
        self.preferences = preferences
        self.db = db
        self.spoon_service = spoon_service
        self.base_search_params = self.prepare_base_params(preferences)
        self.calories_targets = self.get_calories_by_meal(preferences.calories_goal)
        self.days_in_plan = MealPlanConfig.DAYS_IN_PLAN

        logger.debug(f"MealPlanGenerator initialized for user {self.preferences.user_id} with params: {self.base_search_params}")

    def prepare_base_params(self, preferences: UserPreferences) :
        diet = preferences.diet_type.name if preferences.diet_type and preferences.diet_type.id != MealPlanConfig.BALANCE_DIET_ID else None
        intolerances = (
            ",".join(
                intolerance.name.lower() for intolerance in preferences.intolerances
            ) if preferences.intolerances else None
        )

        cuisines = (
            ",".join(
                cuisine.name.lower() for cuisine in preferences.cuisines
            ) if preferences.cuisines else None
        )

        return {"diet": diet, "intolerances": intolerances, "cuisines": cuisines}
    
    def get_calories_by_meal(self, total: float) -> dict[MealSlot, int]:
        return { slot: round(total * pct) for slot, pct in MealPlanConfig.CALORIE_PERCENTAGES.items()}
    
    
    def _select_daily_meals(self, available_recipes: dict[MealSlot, list[Recipe]], days_to_generate: int) -> dict[int, dict[int, Recipe]]:
        final_plan = {}

        breakfast_pool = available_recipes.get(MealSlot.BREAKFAST, [])
        lunch_pool = available_recipes.get(MealSlot.LUNCH, [])
        dinner_pool = available_recipes.get(MealSlot.DINNER, [])

        if not all([breakfast_pool, lunch_pool, dinner_pool]):
            raise MealPlanGeneratorError(
                "Not enough recipe variety to generate a full plan.", 
                code="INSUFFICIENT_RECIPE_VARIETY"
            )
        
        random.shuffle(breakfast_pool)
        random.shuffle(lunch_pool)
        random.shuffle(dinner_pool)

        logger.debug(f"Assembling final plan. Pool sizes - Breakfasts: {len(breakfast_pool)}, Lunches: {len(lunch_pool)}, Dinners: {len(dinner_pool)}")

        used_lunch_ids = set()
        for day_idx in range(days_to_generate):
            daily_meals = {}

            daily_meals[MealSlot.BREAKFAST] = breakfast_pool[day_idx % len(breakfast_pool)]

            selected_lunch = lunch_pool[day_idx % len(lunch_pool)]
            daily_meals[MealSlot.LUNCH] = selected_lunch
            used_lunch_ids.add(selected_lunch.id)

            dinner_candidates = [d for d in dinner_pool if d.id not in used_lunch_ids]
            if not dinner_candidates:
                dinner_candidates = [d for d in dinner_pool if d.id != selected_lunch.id]

            if not dinner_candidates:
                dinner_candidates = dinner_pool

            selected_dinner = dinner_candidates[day_idx % len(dinner_candidates)]
            daily_meals[MealSlot.DINNER] = selected_dinner


            final_plan[day_idx] = {slot.value: recipe for slot, recipe in daily_meals.items()}
            
        return final_plan

    async def _fetch_from_api_with_fallback(
        self,
        meal_slot: MealSlot,
        limit: int,
        exclude_recipe_ids: set[int]
    ) -> list[Recipe]:
        
        target_calories = self.calories_targets.get(meal_slot)
        calorie_range = max(150, target_calories * 0.25)
        min_calories = target_calories - calorie_range
        max_calories = target_calories + calorie_range
        found_recipes = {}
        MAX_ATTEMPTS = 3
        
        for attempt in range(1, MAX_ATTEMPTS + 1):
            current_search_params = self.base_search_params.copy()
            
            if attempt == 2:
                logger.warning(f"API Fallback for {meal_slot.name} (Attempt 2): Removing calorie filter to find more recipes.")
                min_calories, max_calories = None, None
            elif attempt == 3 and "cuisines" in current_search_params:
                logger.warning(f"API Fallback for {meal_slot.name} (Attempt 3): Removing 'cuisines' filter to find more recipes.")
                current_search_params.pop("cuisines", None)

            diet_used_in_query = current_search_params.get("diet")

            api_result = await self.spoon_service.search_recipes(
                type=MealPlanConfig.MEAL_TYPES_SPOONACULAR[meal_slot],
                diet=diet_used_in_query,
                intolerances=current_search_params.get("intolerances"),
                cuisine=current_search_params.get("cuisines"),
                min_calories=min_calories if min_calories is not None else None,
                max_calories=max_calories if max_calories is not None else None,
                number=limit * 3,
                sort="random"
            )

            if not api_result.get("error"):
                for recipe_data in api_result.get("results", []):
                    db_recipe, was_created = get_or_create_spoonacular_recipe(self.db, recipe_data)

                    if db_recipe and diet_used_in_query:
                        is_diet_already_associated = any(
                            dt.name.lower() == diet_used_in_query.lower() 
                            for dt in db_recipe.diet_types
                        )
                        
                        if not is_diet_already_associated:
                            diet_obj = get_or_create_diet_type(self.db, diet_used_in_query)
                            if diet_obj:
                                db_recipe.diet_types.append(diet_obj)
                    
                    if db_recipe and db_recipe.id not in exclude_recipe_ids and db_recipe.id not in found_recipes:
                        found_recipes[db_recipe.id] = db_recipe
                        if len(found_recipes) >= limit:
                            logger.info(f"API fetch for {meal_slot.name} succeeded on attempt {attempt}. Found {len(found_recipes)} recipes.")
                            break
            if len(found_recipes) >= limit:
                logger.info(f"Fallback attempt {attempt} for {meal_slot.name} was successful. Found enough recipes.")
                break 

        self.db.commit()
        return list(found_recipes.values())
    
    async def _find_recipes_for_slot(
        self, 
        meal_slot: MealSlot, 
        limit: int, 
        exclude_recipe_ids: set[int]
    ) -> list[Recipe]:
        """Searches for recipes for a specific meal slot, first in the database and then in Spoonacular if needed"""

        target_calories = self.calories_targets.get(meal_slot)
        calorie_range = max(150, target_calories * 0.25)
        min_calories = target_calories - calorie_range
        max_calories = target_calories + calorie_range
        
        found_recipes = {}
        if not user_has_complex_intolerances(self.preferences):
            logger.info(f"Searching DB for {limit} recipes for {meal_slot.name}.")

            config = MEAL_TYPE_SUGGESTION_CONFIG.get(meal_slot.name.lower(), MEAL_TYPE_SUGGESTION_CONFIG["main course"])
            db_dish_types_to_search = config["db_dish_types"]

            db_suggestions = get_recipe_suggestions_from_db(
                self.db, exclude_recipe_ids, self.preferences, db_dish_types_to_search, limit, min_calories, max_calories
            )
            for recipe in db_suggestions:
                found_recipes[recipe.id] = recipe
            logger.info(f"Found {len(found_recipes)} recipes in DB for {meal_slot.name}.")

        if len(found_recipes) < limit:
            recipes_needed_from_api = limit - len(found_recipes)
            logger.info(f"Not enough recipes in DB for {meal_slot.name}. Fetching {recipes_needed_from_api} more from Spoonacular.")
            current_exclude_ids = set(found_recipes.keys())

            api_recipes = await self._fetch_from_api_with_fallback(meal_slot, recipes_needed_from_api, current_exclude_ids)
            for recipe in api_recipes:
                found_recipes[recipe.id] = recipe

        return list(found_recipes.values())



    async def generate(self) -> tuple[dict, PlanGenerationStatus]:
        recipes_by_meal_slot = {}
        recipe_ids_to_exclude = set()
        for meal_slot in MealSlot:
            required_recipes = self.days_in_plan
            
            fetched_recipes = await self._find_recipes_for_slot(meal_slot, required_recipes, recipe_ids_to_exclude)
            if meal_slot is MealSlot.LUNCH:
                for recipe in fetched_recipes:
                    recipe_ids_to_exclude.add(recipe.id)

            recipes_by_meal_slot[meal_slot] = fetched_recipes

        num_lunches = len(recipes_by_meal_slot.get(MealSlot.LUNCH, []))
        num_dinners = len(recipes_by_meal_slot.get(MealSlot.DINNER, []))
        num_breakfasts = len(recipes_by_meal_slot.get(MealSlot.BREAKFAST, []))

        effective_plan_days = min(num_lunches, num_dinners)
        if effective_plan_days < MealPlanConfig.MINIMUM_VIABLE_DAYS  or num_breakfasts < 2:
            raise MealPlanGeneratorError(
                "Could not find enough recipe variety for a viable plan. Please adjust your preferences.",
                code=ErrorCode.PREFERENCES_TOO_STRICT
            )
        
        days_to_generate = min(effective_plan_days, self.days_in_plan)
        status = PlanGenerationStatus.FULL_SUCCESS if effective_plan_days >= self.days_in_plan else PlanGenerationStatus.PARTIAL_SUCCESS
        
        generated_plan_structure = self._select_daily_meals(recipes_by_meal_slot, days_to_generate)
        
        return (generated_plan_structure, status)
    
