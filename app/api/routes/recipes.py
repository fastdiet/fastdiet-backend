import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.auth import get_current_user, get_language
from app.core.errors import ErrorCode
from app.crud.recipe import get_recipe_by_id, get_recipe_details, get_recipes_by_creator_id
from app.db.db_connection import get_db
from app.models.meal_item import MealItem
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.recipe import RecipeCreate, RecipeDetailResponse, RecipesListResponse
from app.services.recipe import create_recipe_from_user_input, serialize_recipe_detail, serialize_recipe_short_list, update_recipe_in_db


logger = logging.getLogger(__name__)

router = APIRouter(tags=["recipes"], prefix="/recipes")

@router.get("/my-recipes", response_model=RecipesListResponse)
def get_my_recipes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), lang: str = Depends(get_language)):
    """Return all recipes created by the current user"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is fetching their created recipes.")
    recipes = get_recipes_by_creator_id(db, current_user.id)
    translated_recipes = serialize_recipe_short_list(recipes, lang)
    return RecipesListResponse(recipes=translated_recipes)

@router.get("/{recipe_id}", response_model=RecipeDetailResponse)
def get_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    language: str = Depends(get_language),
):
    """Endpoint to get detailed information for a specific recipe"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is fetching details for recipe ID: {recipe_id}.")
    db_recipe = get_recipe_details(db, recipe_id)
    if not db_recipe:
        logger.warning(f"Failed to fetch recipe ID {recipe_id}: Not found.")
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.RECIPE_NOT_FOUND, "message": "Recipe not found"}
        )
    return serialize_recipe_detail(db_recipe, language)

@router.post("/me", response_model=RecipeDetailResponse, status_code=201)
def create_user_recipe(
    recipe_data: RecipeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    language: str = Depends(get_language)
):
    """Endpoint for a user to create a new custom recipe"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is creating a new recipe titled '{recipe_data.title}'.")
    db_recipe = create_recipe_from_user_input(db, recipe_data, current_user.id, language)
    logger.info(f"Successfully created new recipe with ID: {db_recipe.id} for user ID: {current_user.id} ({current_user.username}).")
    return serialize_recipe_detail(db_recipe, language)

@router.put("/me/{recipe_id}", response_model=RecipeDetailResponse)
def update_user_recipe(
    recipe_id: int,
    recipe_data: RecipeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    language: str = Depends(get_language)
):
    """Endpoint for a user to create a new custom recipe"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is attempting to update recipe ID: {recipe_id}.")
    db_recipe = get_recipe_by_id(db, recipe_id)
    if not db_recipe:
        logger.warning(f"Update failed for user ID {current_user.id} ({current_user.username}): Recipe ID {recipe_id} not found.")
        raise HTTPException( status_code=404, detail={"code": ErrorCode.RECIPE_NOT_FOUND, "message": "Recipe not found"})
    
    if db_recipe.creator_id != current_user.id:
        logger.warning(f"Forbidden update attempt by user ID {current_user.id} ({current_user.username}) on recipe ID {recipe_id} (not owner).")
        raise HTTPException( status_code=403, detail={"code": ErrorCode.FORBIDDEN_RECIPE_UPDATE, "message": "You can only update your own recipes"})
    
    if db_recipe.spoonacular_id is not None:
        logger.warning(f"Forbidden update attempt by user ID {current_user.id} ({current_user.username}) on recipe ID {recipe_id}: Cannot update a Spoonacular recipe.")
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.IMPORTED_RECIPE_UPDATE_FORBIDDEN, "message": "Cannot update recipes imported from Spoonacular"}
        )
    
    updated_recipe = update_recipe_in_db(db, db_recipe, recipe_data, language)
    logger.info(f"Recipe ID {recipe_id} updated successfully by user ID {current_user.id} ({current_user.username}).")
    return serialize_recipe_detail(updated_recipe, language)

@router.delete("/me/{recipe_id}", response_model=SuccessResponse)
def delete_user_recipe(recipe_id: int, force: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Endpoint to delete a user's custom recipe"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is attempting to delete recipe ID: {recipe_id}.")
    db_recipe = get_recipe_by_id(db, recipe_id)
    if not db_recipe:
        logger.warning(f"Delete failed for user ID {current_user.id} ({current_user.username}): Recipe ID {recipe_id} not found.")
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.RECIPE_NOT_FOUND, "message": "Recipe not found"}
        )
    
    if db_recipe.creator_id != current_user.id:
        logger.warning(f"Forbidden delete attempt by user ID {current_user.id} ({current_user.username}) on recipe ID {recipe_id} (not owner).")
        raise HTTPException(
            status_code=403,
            detail={"code": ErrorCode.FORBIDDEN_RECIPE_DELETE, "message": "You can only delete your own recipes"}
        )
    
    if db_recipe.spoonacular_id is not None:
        logger.warning(f"Forbidden delete attempt by user ID {current_user.id} ({current_user.username}) on recipe ID {recipe_id}.Cannot delete a Spoonacular recipe.")
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.IMPORTED_RECIPE_DELETE_FORBIDDEN, "message": "Cannot delete recipes imported from Spoonacular"}
        )
    
    linked_meal_items = db.query(MealItem).filter(MealItem.recipe_id == recipe_id).all()

    if linked_meal_items and not force:
        logger.warning(f"Delete failed for recipe ID {recipe_id}: Recipe is linked to meal plan and 'force' is false.")
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.RECIPE_LINKED_TO_MEAL_PLAN, "message": "This recipe is included in your meal plan"}
        )
    
    if linked_meal_items and force:
        logger.info(f"Performing forced delete of recipe ID {recipe_id}, which is linked to {len(linked_meal_items)} meal items.")

    db.delete(db_recipe)
    db.commit()
    logger.info(f"Recipe ID {recipe_id} deleted successfully by user ID {current_user.id} ({current_user.username}).")
    return SuccessResponse(success=True, message="Recipe deleted successfully")


