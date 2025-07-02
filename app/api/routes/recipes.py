from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.crud.recipe import get_recipe_details
from app.db.db_connection import get_db
from app.models.user import User
from app.schemas.recipe import RecipeDetailResponse
from app.services.recipe import recipe_to_response


router = APIRouter(tags=["recipes"], prefix="/recipes")


@router.get("/{recipe_id}", response_model=RecipeDetailResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Endpoint to get detailed information for a specific recipe"""

    db_recipe = get_recipe_details(db, recipe_id)
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe_to_response(db_recipe)