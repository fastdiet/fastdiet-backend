
from sqlalchemy.orm import Session
from app.models import User
from app.schemas.user import UserCreate


def get_user_by_username(db: Session, username: str, ):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str, ):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username_or_email(db: Session, email: str, username: str) -> User | None:
    existing_user = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()
    return existing_user

def create_user(db: Session, user_data: UserCreate) -> User:
    user = User(
        username=user_data.username,
        email=user_data.email,
        name=user_data.name,
        hashed_password=user_data.password,
        auth_method="traditional",
        is_verified=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
