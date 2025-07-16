from sqlalchemy.orm import Session
from app.models.ingredient import Ingredient


def get_or_create_spoonacular_ingredient(db: Session, ingredient_data: dict) -> Ingredient | None:

    ingredient_name = ingredient_data.get("nameClean") or ingredient_data.get("name")
    
    if not ingredient_name:
        return None
    normalized_name = ingredient_name.strip().lower()
    spoon_id = ingredient_data.get("id")
    ingredient = None
    if spoon_id:
        ingredient = db.query(Ingredient).filter(Ingredient.spoonacular_id == spoon_id).first()

    if not ingredient:
        ingredient = db.query(Ingredient).filter(Ingredient.name == normalized_name).first()
        
    if not ingredient:
        ingredient = Ingredient(
                spoonacular_id=spoon_id,
                name=normalized_name,
                image_filename=ingredient_data.get("image"),
                aisle=ingredient_data.get("aisle")
            )
        db.add(ingredient)
        db.flush()
        return ingredient
    
    updated = False
    if ingredient_data.get("image") and ingredient.image_filename != ingredient_data.get("image"):
        ingredient.image_filename = ingredient_data.get("image")
        updated = True
    if ingredient_data.get("aisle") and ingredient.aisle != ingredient_data.get("aisle"):
        ingredient.aisle = ingredient_data.get("aisle")
        updated = True
    if spoon_id and not ingredient.spoonacular_id:
        ingredient.spoonacular_id = spoon_id
        updated = True
    if updated:
        db.flush()

    return ingredient

def get_or_create_ingredient_by_name(db: Session, name: str) -> Ingredient:
    normalized_name = name.strip().lower()
    ingredient = db.query(Ingredient).filter(Ingredient.name == normalized_name).first()

    if not ingredient:
        ingredient = Ingredient(name=normalized_name)
        db.add(ingredient)
        db.flush()
    return ingredient