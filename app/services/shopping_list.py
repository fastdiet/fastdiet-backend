

from collections import defaultdict
from app.models.ingredient import Ingredient
from app.models.meal_plan import MealPlan
from app.schemas.shopping_list import ShoppingListItem
from app.utils.translator import UNIT_TRANSLATOR, translate_unit_to_english


def aggregate_ingredients_from_meal_plan(meal_plan: MealPlan, servings: int | None = None) -> dict:
    aggregated_ingredients = defaultdict(lambda: {"amount": 0.0, "ingredient": None, "unit": ""})
    for meal_item in meal_plan.meal_items or []:
        recipe = meal_item.recipe
        if recipe:
            scaling_factor = 1.0
            if servings is not None and recipe.servings and recipe.servings > 0:
                scaling_factor = servings / recipe.servings

            for ri in recipe.recipes_ingredients:
                if ri.ingredient:
                    key = (ri.ingredient.id, (ri.unit or "").lower())

                    scaled_amount = ri.amount * scaling_factor

                    aggregated_ingredients[key]["amount"] += scaled_amount
                    aggregated_ingredients[key]["ingredient"] = ri.ingredient
                    aggregated_ingredients[key]["unit"] = ri.unit or ""

    return aggregated_ingredients


def partition_shopping_list_items(
    aggregated: dict, language: str
) -> tuple[list[str], dict[str, Ingredient], list[ShoppingListItem]]:
    items_for_api = []
    ingredient_map = {}
    manual_items_data = []

    for data in aggregated.values():
        ingredient = data["ingredient"]
        unit = data["unit"] or ""
        amount = data["amount"]

        can_send_to_api = False
        unit_for_api = unit.strip().lower()

        if ingredient.spoonacular_id:
            if language == "es":
                unit_for_api = translate_unit_to_english(unit_for_api)
            
            if unit_for_api == "" or unit_for_api in UNIT_TRANSLATOR:
                can_send_to_api = True

        if can_send_to_api:
            name_en = ingredient.name_en.strip().lower()
            formatted_item = f"{amount} {unit_for_api} {name_en}".strip().replace("  ", " ")
            items_for_api.append(formatted_item)
            ingredient_map[ingredient.spoonacular_id] = ingredient
        else:
            manual_items_data.append({
                "ingredient": ingredient,
                "amount": amount,
                "unit": unit
            })
            
    return items_for_api, ingredient_map, manual_items_data
