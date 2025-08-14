import asyncio
import logging
from typing import Any
from fastapi import HTTPException
import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class SpoonacularService:
    """
    Service to interact with Spoonacular API
    """
    def __init__(self):
        self.api_key = get_settings().spoonacular_api_key
        self.base_url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
        }
        self.timeout = 20.0
        self.max_retries = 4
        self.base_delay = 0.6

    async def _request_with_retry(self, method: str, endpoint: str, params: dict | None = None, payload: dict | None = None) -> dict[str, Any]:
        """ Makes an HTTP request to the Spoonacular API with automatic retries on rate limits."""
        url = f"{self.base_url}/{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            for attempt in range(self.max_retries):
                try:
                    logger.debug(f"Calling Spoonacular API ({method}). Endpoint: {endpoint}. Attempt: {attempt + 1}/{self.max_retries}")
                    
                    if method.upper() == "GET":
                        response = await client.get(url, params=params)
                    elif method.upper() == "POST":
                        response = await client.post(url, json=payload)
                    else:
                        logger.error(f"Invalid HTTP method '{method}' passed to _request_with_retry.")
                        raise ValueError("Invalid HTTP method specified")

                    response.raise_for_status()
                    
                    remaining_results = response.headers.get("X-Ratelimit-Results-Remaining", "N/A")
                    remaining_tiny_requests = response.headers.get("X-Ratelimit-Tinyrequests-Remaining", "N/A")
                    remaining_requests = response.headers.get("X-Ratelimit-Requests-Remaining", "N/A")
                    logger.info(f"Spoonacular call to '{endpoint}' successful. Rate limit Results remaining: {remaining_results}, Tiny requests remaining: {remaining_tiny_requests}, Requests remaining: {remaining_requests}")
                    return response.json()

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429 and attempt < self.max_retries - 1:
                        delay = self.base_delay * (2 ** attempt)
                        logger.warning(f"Rate limit exceeded on endpoint '{endpoint}'. Retrying in {delay:.2f} seconds...")
                        await asyncio.sleep(delay)
                        continue

                    error_detail = e.response.text
                    logger.error(
                        f"Spoonacular API HTTP error on endpoint '{endpoint}'. Status: {e.response.status_code}. Details: {error_detail}",
                        exc_info=True
                    )
                    raise HTTPException(
                        status_code=e.response.status_code, 
                        detail=f"Error from Spoonacular API: {error_detail}"
                    )
                
                except httpx.RequestError as e:
                    logger.error(
                        f"Network error calling Spoonacular API endpoint '{endpoint}'. Details: {e}",
                        exc_info=True
                    )
                    raise HTTPException(
                        status_code=503, # Service Unavailable
                        detail=f"Service unavailable: could not connect to Spoonacular. Details: {str(e)}"
                    )
        
        logger.error(f"Spoonacular API did not respond from endpoint '{endpoint}' after {self.max_retries} retries.")
        raise HTTPException(status_code=504, detail="Spoonacular API did not respond after multiple retries.")

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
            "number": number
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        logger.info(f"Searching spoonacular recipes with diet: {params.get('diet')}, intolerances: {params.get('intolerances')}")
        return await self._request_with_retry("GET", "recipes/complexSearch", params=params)
    
    async def compute_shopping_list(self, items: list[str]) -> dict[str, Any]:
        if not items:
            logger.info("compute_shopping_list called with no items, returning empty list.")
            return {"aisles": [], "cost": 0.0}
        
        payload = {"items": items}
        logger.debug(f"Computing shopping list with payload: {payload}")
        return await self._request_with_retry("POST", "mealplanner/shopping-list/compute", payload=payload)
    
    async def fetch_ingredients_info(self, spoonacular_id: int):
        logger.info(f"Fetching ingredient info for Spoonacular ID: {spoonacular_id}")
        data = await self._request_with_retry("GET", f"food/ingredients/{spoonacular_id}/information")
        return {
            "name": data.get("name"),
            "image": data.get("image"),
            "aisle": data.get("aisle"),
            "possible_units": data.get("possibleUnits"),
        }