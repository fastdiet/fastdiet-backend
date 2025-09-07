from app.models.ingredient import Ingredient
from app.schemas.ingredient import IngredientShort


def serialize_ingredient_short(ingredient: Ingredient, lang: str) -> IngredientShort:
    return IngredientShort(
        id=ingredient.id,
        name=ingredient.name_es if lang == "es" else ingredient.name_en,
        image_filename=ingredient.image_filename,
        aisle=ingredient.aisle,
    )