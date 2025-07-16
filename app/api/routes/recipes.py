from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core.errors import ErrorCode
from app.crud.recipe import get_recipe_by_id, get_recipe_details, get_recipes_by_creator_id
from app.db.db_connection import get_db
from app.models.meal_item import MealItem
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.recipe import RecipeCreate, RecipeDetailResponse, RecipesListResponse
from app.services.recipe import create_recipe_from_user_input, recipe_to_response


router = APIRouter(tags=["recipes"], prefix="/recipes")

@router.get("/my-recipes", response_model=RecipesListResponse)
def get_my_recipes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return all recipes created by the current user"""
    recipes = get_recipes_by_creator_id(db, current_user.id)
    return RecipesListResponse(recipes=recipes)

@router.get("/{recipe_id}", response_model=RecipeDetailResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Endpoint to get detailed information for a specific recipe"""

    db_recipe = get_recipe_details(db, recipe_id)
    if not db_recipe:
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.RECIPE_NOT_FOUND, "message": "Recipe not found"}
        )
    return recipe_to_response(db_recipe)


@router.post("/me", response_model=RecipeDetailResponse, status_code=201)
def create_user_recipe(
    recipe_data: RecipeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint for a user to create a new custom recipe"""
    db_recipe = create_recipe_from_user_input(db, recipe_data, current_user.id)
    
    return recipe_to_response(db_recipe)

@router.delete("/me/{recipe_id}", response_model=SuccessResponse)
def delete_user_recipe(recipe_id: int, force: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Endpoint to delete a user's custom recipe"""
    db_recipe = get_recipe_by_id(db, recipe_id)
    if not db_recipe:
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.RECIPE_NOT_FOUND, "message": "Recipe not found"}
        )
    
    if db_recipe.creator_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail={"code": ErrorCode.FORBIDDEN_RECIPE_DELETE, "message": "You can only delete your own recipes"}
        )
    
    if db_recipe.spoonacular_id is not None:
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.IMPORTED_RECIPE_DELETE_FORBIDDEN, "message": "Cannot delete recipes imported from Spoonacular"}
        )
    
    linked_meal_items = db.query(MealItem).filter(MealItem.recipe_id == recipe_id).all()

    if linked_meal_items and not force:
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.RECIPE_LINKED_TO_MEAL_PLAN, "message": "This recipe is included in your meal plan"}
        )

    db.delete(db_recipe)
    db.commit()
    
    return SuccessResponse(success=True, message="Recipe deleted successfully")


