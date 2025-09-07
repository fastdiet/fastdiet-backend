from sqlalchemy.orm import Session

from app.crud.diet_type import get_or_create_diet_type
from app.models.diet_type import DietType

def get_or_create_diet_objects(db: Session, spoon_diets: list[str]) -> list[DietType]:
    if not spoon_diets:
        return []

    final_diet_objects = {}
    for diet_name in spoon_diets:
        name_lower = diet_name.lower()

        db_diet = get_or_create_diet_type(db, name_lower)

        if db_diet:
            final_diet_objects[db_diet.id] = db_diet
    
    return list(final_diet_objects.values())

def normalize_diets(api_diets: list[str], recipe_flags: dict) -> list[str]:
    diets_set = set(d.lower() for d in api_diets)

    if "vegan" not in diets_set:
        if "ovo vegetarian" in diets_set and recipe_flags.get("dairyFree"):
            diets_set.add("vegan")
        if "lacto vegetarian" in diets_set and recipe_flags.get("dairyFree"):
            diets_set.add("vegan")
        if "lacto ovo vegetarian" in diets_set:
            diets_set.add("vegan")

    return list(diets_set)