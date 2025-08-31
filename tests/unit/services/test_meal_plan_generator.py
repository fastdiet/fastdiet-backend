import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.core.errors import ErrorCode
from app.services.meal_plan_generator import MealPlanGenerator, MealPlanGeneratorError
from app.models.user_preferences import UserPreferences
from app.models.recipe import Recipe
from app.core.meal_plan_config import PlanGenerationStatus, MealPlanConfig


@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_spoon_service():
    service = MagicMock()
    service.search_recipes = AsyncMock()
    return service

@pytest.fixture
def mock_user_preferences():
    prefs = MagicMock(spec=UserPreferences)
    prefs.user_id = 1
    prefs.calories_goal = 2000.0
    prefs.diet_type = MagicMock(name="Vegetarian", id=1)
    prefs.intolerances = []
    prefs.cuisines = []
    return prefs

def recipe_factory(recipe_id: int, name: str) -> MagicMock:
    recipe = MagicMock(spec=Recipe)
    recipe.id = recipe_id
    recipe.name = name
    return recipe


@pytest.mark.asyncio
class TestMealPlanGenerator:

    async def test_generate_success_from_db_only(
        self, mock_user_preferences, mock_db, mock_spoon_service
    ):
        
        db_recipes = {
            "breakfast": [recipe_factory(i, f"Breakfast {i}") for i in range(1, MealPlanConfig.DAYS_IN_PLAN + 1)],
            "main_course": [recipe_factory(i, f"Lunch/Dinner {i}") for i in range(10, 10 + MealPlanConfig.DAYS_IN_PLAN * 2)],
        }
        
        def db_side_effect(db, exclude, prefs, types, limit, min_c, max_c):
            if "breakfast" in types:
                return db_recipes["breakfast"]
            elif "main course" in types:
                return db_recipes["main_course"]
            return []

        with patch("app.services.meal_plan_generator.get_recipe_suggestions_from_db") as mock_get_db_recipes, \
            patch("app.services.meal_plan_generator.user_has_complex_intolerances", return_value=False):
            
            mock_get_db_recipes.side_effect = db_side_effect
            generator = MealPlanGenerator(mock_user_preferences, mock_db, mock_spoon_service)

            plan, status = await generator.generate()

            assert status == PlanGenerationStatus.FULL_SUCCESS
            assert len(plan) == MealPlanConfig.DAYS_IN_PLAN
            assert 1 in plan[0]
            
            mock_spoon_service.search_recipes.assert_not_called()
            assert mock_get_db_recipes.call_count == 3


    async def test_generate_success_with_api_fallback(
        self, mock_user_preferences, mock_db, mock_spoon_service
    ):
        api_breakfasts_data = [{"id": 101, "title": "API B1"}, {"id": 102, "title": "API B2"}]
        api_main_courses_data = [{"id": 201, "title": "API MC1"}, {"id": 202, "title": "API MC2"}]
        
        async def spoon_side_effect(*args, **kwargs):
            if kwargs.get("type") == "breakfast":
                return {"results": api_breakfasts_data}
            elif kwargs.get("type") == "main course":
                return {"results": api_main_courses_data}
            return {"results": []}
        
        mock_spoon_service.search_recipes.side_effect = spoon_side_effect

        with patch("app.services.meal_plan_generator.get_recipe_suggestions_from_db") as mock_get_db_recipes, \
            patch("app.services.meal_plan_generator.get_or_create_spoonacular_recipe") as mock_get_or_create, \
            patch("app.services.meal_plan_generator.user_has_complex_intolerances", return_value=False):
            
            mock_get_db_recipes.return_value = []
            
            def get_or_create_side_effect(db, recipe_data):
                return recipe_factory(recipe_data['id'], recipe_data['title'])
            mock_get_or_create.side_effect = get_or_create_side_effect

            generator = MealPlanGenerator(mock_user_preferences, mock_db, mock_spoon_service)
            
            plan, status = await generator.generate()

            assert status == PlanGenerationStatus.PARTIAL_SUCCESS
            assert len(plan) == 2
            
            mock_get_db_recipes.assert_called()
            assert mock_spoon_service.search_recipes.call_count == 9

    async def test_generate_fails_with_strict_preferences(
        self, mock_user_preferences, mock_db, mock_spoon_service
    ):
        mock_spoon_service.search_recipes.return_value = {"results": []}

        with patch("app.services.meal_plan_generator.get_recipe_suggestions_from_db") as mock_get_db_recipes, \
            patch("app.services.meal_plan_generator.user_has_complex_intolerances", return_value=False):
            
            mock_get_db_recipes.return_value = []
            generator = MealPlanGenerator(mock_user_preferences, mock_db, mock_spoon_service)

            with pytest.raises(MealPlanGeneratorError) as exc_info:
                await generator.generate()

            assert exc_info.value.code == ErrorCode.PREFERENCES_TOO_STRICT
            mock_get_db_recipes.assert_called()
            mock_spoon_service.search_recipes.assert_called()