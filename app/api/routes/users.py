from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.db_connection import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import update_user


router = APIRouter(tags=["users"], prefix="/users")


@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Endpoint to get the current user's profile"""
    return current_user

@router.put("/", response_model=UserResponse)
def update(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Endpoint to update the user information"""
    return update_user(db, current_user, user_update)





