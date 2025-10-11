from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from app.core.errors import ErrorCode
from app.models import User
from app.schemas.user import UserRegister, UserUpdate
from app.core.security import hash_password
from fastapi import HTTPException
from app.crud.user import create_user, get_user_by_email, get_user_by_username
from app.db.db_connection import get_sync_session
from app.services.user_preferences import get_or_create_user_preferences, recalculate_calories_if_possible

logger = logging.getLogger(__name__)

def register_user(db: Session, user_data: UserRegister) -> User:
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        if existing_user.is_verified:
            logger.warning(f"Registration failed: Email '{user_data.email}' is already registered and verified.")
            raise HTTPException(
                status_code=400,
                detail={"code": ErrorCode.EMAIL_ALREADY_REGISTERED, "message": "Email already registered"}
            )
        
        logger.info(f"User with email '{user_data.email}' (ID: {existing_user.id}) exists but is unverified. New registration attempt.")
        existing_user.hashed_password = hash_password(user_data.password)
        db.commit()
        db.refresh(existing_user)
        return existing_user
    else:
        hashed_password = hash_password(user_data.password)
        user_data.password = hashed_password
        user = create_user(db, user_data)
        logger.info(f"Successfully created new user with email '{user_data.email}', assigned ID: {user.id}.")
        return user

def update_user(db: Session, current_user: User, user_update: UserUpdate):
    updated_fields = user_update.model_dump(exclude_unset=True)

    logger.debug(f"Updating user ID {current_user.id} with fields: {list(updated_fields.keys())}")

    if "username" in updated_fields:
        user_with_same_username = get_user_by_username(db, user_update.username)
        if user_with_same_username and user_with_same_username.id != current_user.id:
            logger.warning(f"Update failed for user ID {current_user.id}: username '{user_update.username}' already exists.")
            raise HTTPException(
                status_code=400,
                detail={"code": ErrorCode.USERNAME_ALREADY_EXISTS, "message": "Username already exists"}
            )
    
    for key, value in updated_fields.items():
        setattr(current_user, key, value)
        
    FIELDS_AFFECTING_CALORIES = {"gender", "age", "weight", "height"}
    affects_calories = any(field in updated_fields for field in FIELDS_AFFECTING_CALORIES)
    
    updated_preferences = None
    if affects_calories:
        logger.info(f"Profile update for user ID {current_user.id} affects calorie goal. Triggering recalculation.")
        preferences = get_or_create_user_preferences(db, current_user.id)
        recalculate_calories_if_possible(db, current_user, preferences)
        updated_preferences = preferences

    return current_user, updated_preferences

def delete_unverified_users(db: Session):
    try:
        time_threshold = datetime.utcnow() - timedelta(minutes=5)
        deleted_count = db.query(User).filter(
            User.is_verified == False,
            User.created_at < time_threshold
        ).delete()
        db.commit()
        logger.debug(f"✅ Deleted {deleted_count} unverified users at {datetime.utcnow()}")
        return {"deleted": deleted_count}
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error deleting unverified users: {e}")
        raise
        
        
        
        
        
        
      
      

        

      