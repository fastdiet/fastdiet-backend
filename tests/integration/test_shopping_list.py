import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
from http import HTTPStatus
from app.api.main import app
from app.core.auth import get_current_user
from app.models.meal_item import MealItem
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.models.ingredient import Ingredient
from app.models.recipes_ingredient import RecipesIngredient
from app.models.user import User



@pytest.fixture
def mock_current_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    return user

@pytest.fixture
def mock_meal_plan_with_ingredients():
    ingredient_chicken = MagicMock(spec=Ingredient, id=1, spoonacular_id=101, name_en="chicken breast", name_es="pechuga de pollo", image_filename="chicken.jpg", aisle="Meat")
    ingredient_salt = MagicMock(spec=Ingredient, id=2, spoonacular_id=None, name_en="special salt", name_es="sal especial", image_filename="salt.jpg", aisle="Spices")

    recipe_ingredient_chicken = MagicMock(spec=RecipesIngredient, ingredient=ingredient_chicken, amount=500.0, unit="g")
    recipe_ingredient_salt = MagicMock(spec=RecipesIngredient, ingredient=ingredient_salt, amount=1.0, unit="pinch")
    
    recipe = MagicMock(spec=Recipe, servings=4)
    recipe.recipes_ingredients = [recipe_ingredient_chicken, recipe_ingredient_salt]

    meal_item = MagicMock(spec=MealItem, recipe=recipe)
    meal_plan = MagicMock(spec=MealPlan, id=99)
    meal_plan.meal_items = [meal_item]
    
    return meal_plan


@pytest.mark.asyncio
class TestGenerateShoppingList:

    async def test_generate_shopping_list_success(
        self, client, mock_current_user, mock_meal_plan_with_ingredients
    ):
        """ Test the successful generation of the shopping list that combines results of the API with manual processed elements """
        
        app.dependency_overrides[get_current_user] = lambda: mock_current_user
        spoonacular_response = {
            "aisles": [{
                "aisle": "Meat",
                "items": [{
                    "id": 1, "ingredientId": 101, "name": "chicken breast",
                    "measures": {"metric": {"amount": 500.0, "unit": "g"}},
                    "cost": 5.0
                }]
            }],
            "cost": 5.0
        }

        with patch("app.api.routes.shopping_lists.get_latest_meal_plan_for_shopping_list", return_value=mock_meal_plan_with_ingredients), \
            patch("app.api.routes.shopping_lists.SpoonacularService") as mock_spoon_service_class:
            
            mock_spoon_instance = mock_spoon_service_class.return_value
            mock_spoon_instance.compute_shopping_list = AsyncMock(return_value=spoonacular_response)

            response = client.get("/shopping_lists/me", headers={"Accept-Language": "es"})

            assert response.status_code == HTTPStatus.OK
            data = response.json()

            assert data["cost"] == 5.0
            assert len(data["aisles"]) > 0

            all_items = [item for aisle in data["aisles"] for item in aisle["items"]]
            item_names = {item["name"] for item in all_items}
            
            assert "pechuga de pollo" in item_names
            assert "sal especial" in item_names
            
            mock_spoon_instance.compute_shopping_list.assert_called_once()
            call_args = mock_spoon_instance.compute_shopping_list.call_args.kwargs
            assert "500.0 g chicken breast" in call_args["items"]


    async def test_generate_shopping_list_no_plan_found(self, client, mock_current_user):
        """ Test the error 404 when the user does not have a meal plan """

        app.dependency_overrides[get_current_user] = lambda: mock_current_user
        with patch("app.api.routes.shopping_lists.get_latest_meal_plan_for_shopping_list", return_value=None):
            response = client.get("/shopping_lists/me")

            assert response.status_code == HTTPStatus.NOT_FOUND
            assert response.json()["detail"]["code"] == "MEAL_PLAN_NOT_FOUND"

    async def test_generate_shopping_list_api_fails_gracefully(
        self, client, mock_current_user, mock_meal_plan_with_ingredients
    ):
        app.dependency_overrides[get_current_user] = lambda: mock_current_user
        with patch("app.api.routes.shopping_lists.get_latest_meal_plan_for_shopping_list", return_value=mock_meal_plan_with_ingredients), \
            patch("app.api.routes.shopping_lists.SpoonacularService") as mock_spoon_service_class:

            mock_spoon_instance = mock_spoon_service_class.return_value
            mock_spoon_instance.compute_shopping_list = AsyncMock(side_effect=HTTPException(status_code=500, detail="API down"))

            response = client.get("/shopping_lists/me", headers={"Accept-Language": "es"})

            assert response.status_code == HTTPStatus.OK
            data = response.json()
            
            assert len(data["aisles"]) == 1
            assert len(data["aisles"][0]["items"]) == 1
            assert data["aisles"][0]["items"][0]["name"] == "sal especial"
            
            all_item_names = {item["name"] for aisle in data["aisles"] for item in aisle["items"]}
            assert "pechuga de pollo" not in all_item_names
            
            assert data["cost"] == 0.0