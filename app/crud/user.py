
from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.models import User
from app.schemas.user import UserRegister


# Function to get a user by username
def get_user_by_username(db: Session, username: str, ) -> User | None:
    return db.query(User).filter(User.username == username).first()

# Function to get a user by email
def get_user_by_email(db: Session, email: str, ) -> User | None:
    return db.query(User).filter(User.email == email).first()

# Function to get a user by ID
def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

# Function to get a user by username or email
def get_user_by_username_or_email(db: Session, email: str, username: str) -> User | None:
    existing_user = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()
    return existing_user

# Function to create a new user
def create_user(db: Session, user_data: UserRegister) -> User:
    user = User(
        email=user_data.email,
        hashed_password=user_data.password,
        auth_method="traditional",
        is_verified=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_google_user(db: Session, email: str, sub: str) -> User:
    user = User(
        email=email,
        auth_method="google",
        sub=sub,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_google_user(db: Session, db_user: User, sub: str) -> User:
    db_user.sub = sub
    db_user.auth_method = "google"
    db_user.is_verified = True
    db.commit()
    db.refresh(db_user)
    return db_user
