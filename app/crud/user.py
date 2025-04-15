
from sqlalchemy.orm import Session
from app.models import User
from app.schemas.user import UserCreate
from app.services.password_service import hash_password
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError


def get_user_by_username(db: Session, username: str, ):
    return db.query(User).filter(User.username == username).first()



def register_user(db: Session, user_data: UserCreate) -> User:

    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if user_data.username and db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = hash_password(user_data.password)

    user = User(
        username=user_data.username,
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        auth_method="traditional",
        is_verified=False,
    )

    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already in use")

    return user