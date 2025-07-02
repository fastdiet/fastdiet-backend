from sqlalchemy.orm import Session

from app.models.ingredient import Ingredient


def get_or_create_ingredient(db: Session, ingredient_data: dict) -> Ingredient | None:

    ingredient_name = ingredient_data.get("nameClean") or ingredient_data.get("name")
    if not ingredient_name:
        return None

    spoon_id = ingredient_data.get("id")
    ingredient = None
    if spoon_id:
        ingredient = db.query(Ingredient).filter(Ingredient.spoonacular_id == spoon_id).first()

    if not ingredient:
        ingredient = db.query(Ingredient).filter(Ingredient.name.ilike(ingredient_name.strip().lower())).first()
        
        if not ingredient:
            ingredient = Ingredient(
                    spoonacular_id=spoon_id,
                    name=ingredient_name.strip().capitalize(),
                    image_filename=ingredient_data.get("image"),
                    aisle=ingredient_data.get("aisle")
                )
            db.add(ingredient)
            db.flush()
            return ingredient
    if ingredient: 
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
            db.add(ingredient)
            db.flush()

    return ingredient