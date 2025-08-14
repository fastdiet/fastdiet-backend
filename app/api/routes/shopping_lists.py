


from collections import defaultdict
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.auth import get_current_user, get_language
from app.core.errors import ErrorCode
from app.crud.ingredient import get_ingredient_by_spoonacular_id
from app.crud.meal_plan import get_latest_meal_plan_for_shopping_list
from app.db.db_connection import get_db
from app.models.user import User
from app.schemas.shopping_list import Aisle, ShoppingListItem, ShoppingListResponse
from app.services.shopping_list import aggregate_ingredients_from_meal_plan, partition_shopping_list_items
from app.services.spoonacular import SpoonacularService
from app.utils.translator import translate_measures_for_shopping_list



logger = logging.getLogger(__name__)

router = APIRouter(tags=["shopping_lists"], prefix="/shopping_lists")

@router.get("/me", response_model=ShoppingListResponse)
async def generate_shopping_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    language: str = Depends(get_language)
):
    """Endpoint to generate the shopping list of the meal plan"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) requested their shopping list in language '{language}'.")
    meal_plan = get_latest_meal_plan_for_shopping_list(db, current_user.id)
    if not meal_plan:
        logger.warning(f"Shopping list generation failed for user ID {current_user.id} ({current_user.username}): No meal plan found.") 
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.MEAL_PLAN_NOT_FOUND, "message": "Meal Plan not found"}
        )
    

    logger.info(f"Generating shopping list from meal plan ID: {meal_plan.id} for user ID: {current_user.id} ({current_user.username}).")
    aggregated_ingredients = aggregate_ingredients_from_meal_plan(meal_plan)
    if not aggregated_ingredients:
        logger.info(f"No ingredients found in meal plan ID: {meal_plan.id}. Returning empty shopping list.")
        return ShoppingListResponse(aisles=[], cost=0.0)
    
    
    items_for_api, ingredient_map, manual_items_data = partition_shopping_list_items(aggregated_ingredients, language)
    spoonacular_data = {"aisles": [], "cost": 0.0}

    if items_for_api:
        spoonacular_service = SpoonacularService()
        try:
            logger.info(f"Sending {len(items_for_api)} items to Spoonacular API for shopping list computation.")
            spoonacular_data = await spoonacular_service.compute_shopping_list(items=items_for_api)
            logger.info(f"Successfully received shopping list data from Spoonacular for user ID {current_user.id}.")
        except HTTPException as e:
            logger.warning(f"Spoonacular API call failed for user ID {current_user.id} ({current_user.username}). Status: {e.status_code}. Detail: {e.detail}. Proceeding with manual items.")

    final_aisles = defaultdict(list)
    
    for aisle in spoonacular_data.get("aisles", []):
        for item in aisle.get("items", []):
            spoonacular_id = item.get("ingredientId")
            local_ingredient = ingredient_map.get(spoonacular_id)
            logger.debug(f"Processing Spoonacular Shopping list item '{item.get('name')}' id {spoonacular_id} for user ID {current_user.id} ({current_user.username})")
            if local_ingredient:
                item["image_filename"] = local_ingredient.image_filename
                item["ingredientId"] = local_ingredient.id
                aisle_name = local_ingredient.aisle or aisle.get("aisle")
                if language == "es":
                    item["name"] = local_ingredient.name_es
                    item["measures"] = translate_measures_for_shopping_list(item.get("measures"), "es")
                else:
                    item["name"] = local_ingredient.name_en
                    item["measures"] = translate_measures_for_shopping_list(item.get("measures"), "en")
            else:
                db_ingredient = get_ingredient_by_spoonacular_id(db, spoonacular_id)
                if db_ingredient:
                    item["image_filename"] = db_ingredient.image_filename
                    item["ingredientId"] = db_ingredient.id
                    aisle_name = db_ingredient.aisle or aisle.get("aisle")
                    if language == "es":
                        item["name"] = db_ingredient.name_es
                        item["measures"] = translate_measures_for_shopping_list(item.get("measures"), "es")
                    else:
                        item["name"] = db_ingredient.name_en
                        item["measures"] = translate_measures_for_shopping_list(item.get("measures"), "en")
                
            final_aisles[aisle_name].append(ShoppingListItem(**item))

    for manual_item_data in manual_items_data:
        ingredient = manual_item_data["ingredient"]
        amount = manual_item_data["amount"]
        unit = manual_item_data["unit"]
        item_name = ingredient.name_es if language == "es" and ingredient.name_es else ingredient.name_en
        logger.debug(f"Processing Manual Shopping list item '{item_name}' for user ID {current_user.id} ({current_user.username})")
        
        manual_item = ShoppingListItem(
            name=item_name,
            ingredientId=ingredient.id,
            image_filename=ingredient.image_filename,
            aisle=ingredient.aisle or "Generic",
            cost=0.0,
            pantryItem=False,
            amount=amount,
            unit=unit,
            measures={
                "metric": {"amount": amount, "unit": unit},
                "us": {"amount": amount, "unit": unit},
            }
            
        )
        final_aisles[manual_item.aisle].append(manual_item)

    response_aisles = [
        Aisle(aisle=aisle_name, items=items_list)
        for aisle_name, items_list in final_aisles.items()
    ]
    logger.info(f"Successfully generated shopping list for user ID {current_user.id} ({current_user.username}) with {len(response_aisles)} aisles.")
    return ShoppingListResponse(aisles=response_aisles, cost=spoonacular_data.get("cost", 0.0))

