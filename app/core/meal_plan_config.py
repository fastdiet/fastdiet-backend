

from enum import Enum


class MealPlanGeneratorError(ValueError):
    def __init__(self, message, code="MEAL_PLAN_GENERATION_FAILED"):
        super().__init__(message)
        self.code = code

class MealSlot(Enum):
    BREAKFAST = 0
    LUNCH = 1  
    DINNER = 2

class PlanGenerationStatus(Enum):
    FULL_SUCCESS = "FULL_SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"

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
    BALANCE_DIET_ID = 1
    VEGETARIAN_DIET_ID = 2
    VEGAN_DIET_ID = 3
    GLUTEN_FREE_DIET_ID = 4
    DAIRY_FREE_DIET_ID = 5
    LOW_FODMAP_DIET_ID = 12
    CALORIE_SEARCH_RANGE = 0
    DAYS_IN_PLAN = 5
    MINIMUM_VIABLE_DAYS = 1

MEAL_TYPE_SUGGESTION_CONFIG = {
    "breakfast":  {"db_dish_types": ["breakfast"], "spoonacular_type": "breakfast"},
    "lunch":      {"db_dish_types": ["main course", "salad", "soup"], "spoonacular_type": "main course"},
    "dinner":     {"db_dish_types": ["main course", "salad", "soup"], "spoonacular_type": "main course"},
    "main course":  {"db_dish_types": ["main course", "salad", "soup"], "spoonacular_type": "main course"},
    "snack":      {"db_dish_types": ["snack", "fingerfood"], "spoonacular_type": "snack"},
    "dessert":    {"db_dish_types": ["dessert"], "spoonacular_type": "dessert"},
    "salad":      {"db_dish_types": ["salad"], "spoonacular_type": "salad"},
    "beverage":   {"db_dish_types": ["beverage", "drink"], "spoonacular_type": "beverage"},
    "appetizer":  {"db_dish_types": ["appetizer", "side dish"], "spoonacular_type": "appetizer"},
    "soup":       {"db_dish_types": ["soup"], "spoonacular_type": "soup"},
    "side dish":  {"db_dish_types": ["side dish"], "spoonacular_type": "side dish"},
}