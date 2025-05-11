from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.db_connection import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import update_user
from app.services.user_preferences import update_cuisine_preferences, update_diet, update_intolerance_preferences
from app.schemas.user_preferences import CuisineRegionUpdate, IntoleranceUpdate, UserPreferencesResponse, DietTypeUpdate


router = APIRouter(tags=["users_preferences"], prefix="/user_preferences")

@router.patch("/diet-type", response_model=UserPreferencesResponse)
async def update_diet_type(
    diet_update: DietTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's diet type preference"""
    preferences = update_diet(db, current_user, diet_update)
    
    return preferences

@router.patch("/cuisine-types", response_model=UserPreferencesResponse)
async def update_cuisine_types(
    cuisine_update: CuisineRegionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's cuisine type preferences"""
    preferences = update_cuisine_preferences(db, current_user, cuisine_update)
    
    return preferences

@router.patch("/intolerances", response_model=UserPreferencesResponse)
async def update_intolerances(
    intolerance_update: IntoleranceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint to update user's intoleraces"""
    preferences = update_intolerance_preferences(db, current_user, intolerance_update)
    
    return preferences