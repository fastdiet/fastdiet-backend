from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import User
from app.schemas.user import UserRegister, UserUpdate
from app.core.security import hash_password
from fastapi import HTTPException
from app.crud.user import create_user, get_user_by_email, get_user_by_username
from app.db.db_connection import get_sync_session
from app.services.user_preferences import get_or_create_user_preferences, recalculate_calories_if_possible

# Function to register a new user
def register_user(db: Session, user_data: UserRegister) -> User:
     existing_user = get_user_by_email(db, user_data.email)
     if existing_user:
        if existing_user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered")
        existing_user.hashed_password = hash_password(user_data.password)
        db.commit()
        db.refresh(existing_user)
        return existing_user
     else:
        hashed_password = hash_password(user_data.password)
        user_data.password = hashed_password
        user = create_user(db, user_data)
        return user

def update_user(db: Session, current_user: User, user_update: UserUpdate) -> User:
    if user_update.username:
        user_with_same_username = get_user_by_username(db, user_update.username)
        if user_with_same_username and user_with_same_username.id != current_user.id:
            raise HTTPException(status_code=400, detail="Username already exists")
        
      
    updated_fields = user_update.model_dump(exclude_none=True)
    fields_affecting_calories = {"gender", "age", "weight", "height"}
    affects_calories = any(field in updated_fields for field in fields_affecting_calories)
      
    for key, value in updated_fields.items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)

    if affects_calories:
        preferences = get_or_create_user_preferences(db, current_user.id)
        recalculate_calories_if_possible(db, current_user, preferences)
        
    return current_user

def delete_unverified_users():
    with next(get_sync_session()) as db:
        try:
            time_threshold = datetime.utcnow() - timedelta(minutes=5)
            deleted_count = db.query(User).filter(
                User.is_verified == False,
                User.created_at < time_threshold
            ).delete()
            db.commit()
            print(f"✅ Deleted {deleted_count} unverified users at {datetime.utcnow()}")
        except Exception as e:
            db.rollback()
            print(f"❌ Error deleting unverified users: {e}")
        finally:
            db.close()
        
        
        
      
      

        

      