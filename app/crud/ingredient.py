from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.ingredient import Ingredient
from app.utils.translator import translate_text


def get_or_create_spoonacular_ingredient(db: Session, ingredient_data: dict) -> Ingredient | None:

    name_en = ingredient_data.get("nameClean") or ingredient_data.get("name")
    if not name_en:
        return None
    
    normalized_name_en = name_en.strip().lower()
    spoon_id = ingredient_data.get("id")
    ingredient = None
    if spoon_id:
        ingredient = db.query(Ingredient).filter(Ingredient.spoonacular_id == spoon_id).first()

    if not ingredient:
        ingredient = db.query(Ingredient).filter(Ingredient.name_en == normalized_name_en).first()
        
    if not ingredient:
        name_es = translate_text(normalized_name_en, target_language='es')
        ingredient = Ingredient(
            spoonacular_id=spoon_id,
            name_en=normalized_name_en,
            name_es=name_es.strip().lower() if name_es else None,
            image_filename=ingredient_data.get("image"),
            aisle=ingredient_data.get("aisle")
        )
        db.add(ingredient)
        db.flush()
        print(f"\n🍕CREATED INGREDIENT: {ingredient.id} {ingredient.name_en} ||||||  {ingredient.name_en}\n")
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

def get_or_create_ingredient_by_name(db: Session, name: str, lang: str) -> Ingredient:
    normalized_name = name.strip().lower()

    if lang == "es":
        query_column = Ingredient.name_es
    else:
        query_column = Ingredient.name_en

    ingredient = db.query(Ingredient).filter(func.lower(query_column) == normalized_name).first()

    if not ingredient:
        create_payload = {
            "name_es": normalized_name,
            "name_en": normalized_name 
        }
        ingredient = Ingredient(**create_payload)
        db.add(ingredient)
        db.flush()
    return ingredient

def get_ingredient_by_spoonacular_id(db: Session, spoon_id: int) -> Ingredient | None:
    ingredient = db.query(Ingredient).filter(Ingredient.spoonacular_id == spoon_id).first()
    return ingredient