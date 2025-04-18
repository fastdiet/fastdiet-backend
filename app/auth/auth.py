from datetime import datetime, timedelta
import secrets
from fastapi import  Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.services.password import verify_password
from app.schemas.token import TokenResponse
from jose import JWTError, jwt
from app.core.config import get_settings
from app.crud.user import get_user_by_id, get_user_by_username
from sqlalchemy.orm import Session
from app.db.db_connection import get_db
from app.models import User
from app.crud.refresh_token import create_refresh_token_in_db, get_valid_refresh_token    
from app.models.refresh_token import RefreshToken


settings = get_settings()
JWT_SECRET_KEY = settings.jwt_secret_key
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 60


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# Function to create a new access token 
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# Function to create a new refresh token
def create_refresh_token(user_id: int, db: Session) -> str:
    token = secrets.token_urlsafe(64)
    expires = datetime.utcnow() + timedelta(days=7)

    db_token = create_refresh_token_in_db(
        db=db,
        token=token,
        user_id=user_id,
        expires_at=expires
    )
    
    return token

# Function to decode the JWT token and extract the user information
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    return user

# Function to authenticate the user using username and password
def authenticate_user(db: Session, username: str, password: str) -> TokenResponse:
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="User not verified")
    
    access_token = create_access_token(data={"sub": str(user.id)},)
    refresh_token = create_refresh_token(user.id, db)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )

# Function to refresh the access token using a valid refresh token
def refresh_user_token(db: Session, refresh_token: str) -> TokenResponse:
    db_token = get_valid_refresh_token(db, refresh_token)
    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    user = get_user_by_id(db, db_token.user_id)
    if not user:
        db_token.is_revoked = True
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db_token.is_revoked = True
    db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(user.id, db)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )
    


