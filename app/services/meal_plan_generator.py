from enum import Enum
import random
from app.models.user_preferences import UserPreferences
from app.services.spoonacular import SpoonacularService

class MealPlanGeneratorError(ValueError):
    pass

class MealSlot(Enum):
    BREAKFAST = 0
    LUNCH = 1  
    DINNER = 2

class MealPlanConfig:
    MEAL_TYPES_SPOONACULAR = {
        MealSlot.BREAKFAST: "breakfast",
        MealSlot.LUNCH: "main course", 
        MealSlot.DINNER: "main course"
    }
    
    CALORIE_PERCENTAGES = {
        MealSlot.BREAKFAST: 0.25,
        MealSlot.LUNCH: 0.40,
        MealSlot.DINNER: 0.35
    }
    
    CALORIE_SEARCH_RANGE = 250
    DAYS_IN_PLAN = 5
    RECIPES_TO_FETCH = {
        MealSlot.BREAKFAST: DAYS_IN_PLAN,        
        MealSlot.LUNCH: DAYS_IN_PLAN * 2,         
        MealSlot.DINNER: DAYS_IN_PLAN * 2          
    }
    

class MealPlanGenerator:
    def __init__(self, preferences: UserPreferences, spoon_service: SpoonacularService):
        self.preferences = preferences
        self.spoon_service = spoon_service
        self.base_search_params = self._prepare_base_params(preferences)
        self.calories_targets = self._get_calories_by_meal(preferences.calories_goal)
        self.days_in_plan = MealPlanConfig.DAYS_IN_PLAN

    def _prepare_base_params(self, preferences: UserPreferences) :
        diet = preferences.diet_type.name if preferences.diet_type and preferences.diet_type.id != 1 else None
        intolerances = (
            ",".join(
                i.intolerance.name.lower()
                for i in preferences.user_preferences_intolerances
            )
            if preferences.user_preferences_intolerances
            else None
        )

        cuisines = (
            ",".join(
                c.cuisine.name.lower()
                for c in preferences.user_preferences_cuisines
            )
            if preferences.user_preferences_cuisines
            else None
        )

        return {"diet": diet, "intolerances": intolerances, "cuisines": cuisines}
    
    def _get_calories_by_meal(self, total: float) -> dict[MealSlot, int]:
        return { slot: round(total * pct) for slot, pct in MealPlanConfig.CALORIE_PERCENTAGES.items()}
    
    async def _fetch_recipes_for_slot_with_fallback(self, meal_slot: MealSlot, target_calories: int, attempt: int = 1) -> list[dict]:
        current_search_params = self.base_search_params.copy()
        
        if attempt == 2 and "cuisines" in current_search_params:
            print(f"Fallback attempt 2 for {meal_slot.name}: Removing cuisines.")
            current_search_params.pop("cuisines", None)

        api_result = await self.spoon_service.search_recipes(
            type=MealPlanConfig.MEAL_TYPES_SPOONACULAR[meal_slot],
            diet=current_search_params.get("diet"),
            intolerances=current_search_params.get("intolerances"),
            cuisine=current_search_params.get("cuisines"),
            min_calories= target_calories - MealPlanConfig.CALORIE_SEARCH_RANGE,
            max_calories= target_calories + MealPlanConfig.CALORIE_SEARCH_RANGE,
            number=MealPlanConfig.RECIPES_TO_FETCH[meal_slot],
            sort="random"
        )
        
        if api_result.get("error"):
             print(f"Spoonacular API error for {meal_slot.name}: {api_result['error']}")
             return []
        

        recipes = api_result.get("results", [])

        unique_recipes = []
        seen_ids = set()
        for recipe in recipes:
            recipe_id = recipe.get('id')
            if recipe_id and recipe_id not in seen_ids:
                unique_recipes.append(recipe)
                seen_ids.add(recipe_id)

        return unique_recipes
    
    async def _fetch_all_recipes_for_plan(self) -> dict[MealSlot, list[dict]]:
        recipes_by_meal_slot = {}
        MAX_FETCH_ATTEMPTS = 2

        for meal_slot in MealSlot:
            target_calories = self.calories_targets[meal_slot]
            required_unique_recipes = 1 if meal_slot == MealSlot.BREAKFAST else self.days_in_plan
            fetched_recipes_for_slot = []
            for attempt in range(1, MAX_FETCH_ATTEMPTS + 1):
                print(f"Fetching recipes for {meal_slot.name}, target_calories={target_calories}, attempt={attempt}")
                fetched_recipes_for_slot = await self._fetch_recipes_for_slot_with_fallback(meal_slot, target_calories, attempt)
                
                if len(fetched_recipes_for_slot) >= required_unique_recipes:
                    print(f"Successfully fetched {len(fetched_recipes_for_slot)} recipes for {meal_slot.name}")
                    break
                elif attempt == MAX_FETCH_ATTEMPTS:
                    error_msg = (f"Insufficient unique recipes for {meal_slot.name}")
                    print(error_msg)
                    raise MealPlanGeneratorError(error_msg)
            
            recipes_by_meal_slot[meal_slot] = fetched_recipes_for_slot
                
        return recipes_by_meal_slot
    
    
    def _select_daily_meals(self, available_recipes: dict[MealSlot, list[dict]]) -> dict[int, dict[MealSlot, dict]]:
        final_plan = {}

        breakfast_pool = available_recipes.get(MealSlot.BREAKFAST)
        lunch_pool = available_recipes.get(MealSlot.LUNCH)
        dinner_pool = available_recipes.get(MealSlot.DINNER)

        used_lunchs = []
        used_dinners = []

        for day_idx in range(self.days_in_plan):
            daily_meals = {}

            daily_meals[MealSlot.BREAKFAST] = random.choice(breakfast_pool)

            selected_lunch = lunch_pool[day_idx]

            used_lunchs.append(selected_lunch)
            daily_meals[MealSlot.LUNCH] = selected_lunch
            
            dinner_candidates = [d for d in dinner_pool if d not in used_dinners and d not in used_lunchs]

            if not dinner_candidates:
               dinner_candidates = [d for d in dinner_pool if d not in used_dinners and d['id'] != selected_lunch['id']]

            if not dinner_candidates:
                dinner_candidates = [d for d in dinner_pool if d['id'] != selected_lunch['id']]

            if not dinner_candidates:
                raise MealPlanGeneratorError("No dinner options available")
            
            used_dinners.append(dinner_candidates[0])
            daily_meals[MealSlot.DINNER] = dinner_candidates[0]
            

            final_plan[day_idx] = {slot.value: recipe for slot, recipe in daily_meals.items()}
            
        return final_plan



    async def generate(self) -> dict[int, dict[int, dict]]:
        print(f"Generating meal plan for user {self.preferences.user_id} with goal {self.preferences.calories_goal} kcal.")
        
        available_recipes = await self._fetch_all_recipes_for_plan() 
        generated_plan_structure = self._select_daily_meals(available_recipes)
        
        print(f"Successfully generated meal plan structure for user {self.preferences.user_id}")
        return generated_plan_structure

    
    
    
    
    
