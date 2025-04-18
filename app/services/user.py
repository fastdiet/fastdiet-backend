from sqlalchemy.orm import Session
from app.models import User
from app.schemas.user import UserCreate
from app.services.password import hash_password
from fastapi import HTTPException
from app.crud.user import create_user, get_user_by_username_or_email

# Function to register a new user
def register_user(db: Session, user_data: UserCreate) -> User:

    if user_data.username:
        user_data.username = user_data.username.strip().lower()
    user_data.email = user_data.email.strip().lower()
    existing_user = get_user_by_username_or_email(db, user_data.email, user_data.username)

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        if existing_user.username == user_data.username:
            raise HTTPException(status_code=400, detail="Username already taken")
        
    if not user_data.password or not user_data.username:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    hashed_password = hash_password(user_data.password)
    user_data.password = hashed_password
    user = create_user(db, user_data)

    return user