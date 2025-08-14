import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.errors import ErrorCode
from app.core.security import hash_password, verify_password
from app.db.db_connection import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.user import PasswordUpdate, UserResponse, UserUpdate, UserWithCaloriesResponse
from app.services.user import update_user


logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"], prefix="/users")

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Endpoint to get the current user's profile"""
    logger.info(f"Fetching profile for user ID: {current_user.id} ({current_user.username})")
    return current_user

@router.delete("/me", status_code=204)
def delete_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Endpoint to delete the current user's profile"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is requesting account deletion.")
    db.delete(current_user)
    db.commit()
    logger.info(f"Account for user ID: {current_user.id} ({current_user.username}) has been deleted successfully.")
    return None


@router.put("/change-password", response_model=SuccessResponse)
def change_password(passwords: PasswordUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Endpoint to change the password from the user's profile"""

    logger.info(f"User ID: {current_user.id} ({current_user.username}) is attempting to change password.")
    if verify_password(passwords.current_password, current_user.hashed_password):
        current_user.hashed_password = hash_password(passwords.new_password)
        db.commit()

        logger.info(f"Password changed successfully for user ID: {current_user.id} ({current_user.username}).")
        return SuccessResponse(success=True, message="Password changed successfully")
    else:
        logger.warning(f"Password change failed for user ID: {current_user.id} ({current_user.username}). Incorrect current password provided.")
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.INCORRECT_CURRENT_PASSWORD, "message": "Incorrect current password"}
        )

    

@router.patch("/", response_model=UserWithCaloriesResponse)
def update(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Endpoint to update the user information"""

    logger.info(f"User ID: {current_user.id} is updating their profile information.")

    updated_user, updated_preferences = update_user(db, current_user, user_update)
    db.commit()
    db.refresh(updated_user)

    calories_goal = None
    if updated_preferences:
        db.refresh(updated_preferences)
        calories_goal = updated_preferences.calories_goal

    logger.info(f"Profile for user ID: {current_user.id} updated successfully.")
        
    return UserWithCaloriesResponse(
        user=updated_user,
        calories_goal=calories_goal
    )





