from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password
from app.db.db_connection import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.user import PasswordUpdate, UserResponse, UserUpdate, UserWithCaloriesResponse
from app.services.user import update_user


router = APIRouter(tags=["users"], prefix="/users")


@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Endpoint to get the current user's profile"""
    return current_user

@router.delete("/me", status_code=204)
def delete_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Endpoint to delete the current user's profile"""
    db.delete(current_user)
    db.commit()
    return None


@router.put("/change-password", response_model=SuccessResponse)
def change_password(passwords: PasswordUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Endpoint to change the password from the user's profile"""
    
    if verify_password(passwords.current_password, current_user.hashed_password):
        current_user.hashed_password = hash_password(passwords.new_password)
        db.commit()

        return SuccessResponse(success=True, message="Password changed successfully")
    else:
        raise HTTPException(status_code=400, detail="Incorrect current password")

    

@router.patch("/", response_model=UserWithCaloriesResponse)
def update(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Endpoint to update the user information"""
    updated_user, updated_preferences = update_user(db, current_user, user_update)

    db.commit()
    db.refresh(updated_user)

    calories_goal = None
    if updated_preferences:
        db.refresh(updated_preferences)
        calories_goal = updated_preferences.calories_goal
        
    return UserWithCaloriesResponse(
        user=updated_user,
        calories_goal=calories_goal
    )





