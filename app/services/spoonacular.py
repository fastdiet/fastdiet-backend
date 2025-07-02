from typing import Any
import httpx
from app.core.config import get_settings

class SpoonacularService:
    def __init__(self):
        self.api_key = get_settings().spoonacular_api_key
        self.base_url = "https://api.spoonacular.com"

    async def _make_request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        all_params = {"apiKey": self.api_key, **params}

        url = f"{self.base_url}/{endpoint}"
        safe_params = {k: v for k, v in all_params.items() if k != "apiKey"}
        print(f"Calling Spoonacular API: {url} with params: {safe_params}")

        async with httpx.AsyncClient(timeout=10.0) as client: 
            try:
                response = await client.get(url, params=all_params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"Spoonacular API HTTP error: {e.response.status_code} - {e.response.text}")
                return {"results": [], "error": f"API error: {e.response.status_code}", "details": e.response.text}
            except httpx.RequestError as e:
                print(f"Error calling Spoonacular API: {e}")
                return {"results": [], "error": f"Request error: {str(e)}"}
            except Exception as e:
                print(f"Unexpected error during Spoonacular API call: {e}")
                return {"results": [], "error": "Unexpected API error"}

    async def search_recipes(
        self,
        diet: str | None = None,
        intolerances: str | None = None,
        cuisine: str | None = None,
        type: str | None = None,
        min_calories: float | None = None,
        max_calories: float | None = None,
        sort: str = "random",
        sort_direction: str = "desc",
        fill_ingredients: bool = True,
        add_recipe_information: bool = True,
        add_recipe_instructions: bool = True,
        add_recipe_nutrition: bool = True,
        number: int = 10
    ) -> dict[str, Any]:
        params = {
            "diet": diet,
            "intolerances": intolerances,
            "cuisine": cuisine,
            "type": type,
            "minCalories": min_calories,
            "maxCalories": max_calories,
            "sort": sort,
            "sortDirection": sort_direction,
            "addRecipeInformation": add_recipe_information,
            "addRecipeInstructions": add_recipe_instructions,
            "addRecipeNutrition": add_recipe_nutrition,
            "fillIngredients": fill_ingredients,
            "number": number,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return await self._make_request("recipes/complexSearch", params)
                