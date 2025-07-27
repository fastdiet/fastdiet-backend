from sqlalchemy.orm import Session

from app.crud.diet_type import get_or_create_diet_type
from app.models.diet_type import DietType

def get_or_create_diet_objects(db: Session, spoon_diets: list[str]) -> list[DietType]:
    if not spoon_diets:
        return []

    DIET_TRADUCTOR = {
        "gluten free": "Gluten Free",
        "ketogenic": "Ketogenic",
        "vegetarian": "Vegetarian",
        "lacto-vegetarian": "Lacto-Vegetarian",
        "ovo-vegetarian": "Ovo-Vegetarian",
        "vegan": "Vegan",
        "pescetarian": "Pescetarian",
        "pescatarian": "Pescetarian",
        "paleo": "Paleo",
        "paleolithic": "Paleo",
        "primal": "Primal",
        "low fodmap": "Low FODMAP",
        "fodmap friendly": "Low FODMAP",
        "whole30": "Whole30",
        "whole 30": "Whole30",
        "lacto ovo vegetarian": "Lacto-Vegetarian",
        "dairy free": None, 
    }
    
    final_diet_objects = {}
    for diet_name in spoon_diets:
        name_lower = diet_name.lower()
        translated_name = DIET_TRADUCTOR.get(name_lower)
        if translated_name is None and name_lower in DIET_TRADUCTOR:
            continue 

        diet_name_to_process = translated_name or diet_name.capitalize()

        db_diet = get_or_create_diet_type(db, diet_name_to_process)

        if db_diet:
            final_diet_objects[db_diet.id] = db_diet
    
    return list(final_diet_objects.values())