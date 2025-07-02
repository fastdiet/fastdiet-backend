from datetime import datetime, timedelta
import secrets
from fastapi import  Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from app.core.security import verify_password
from app.schemas.token import AuthResponse, TokenResponse
from jose import JWTError, jwt
from app.core.config import get_settings
from app.crud.user import create_google_user, get_user_by_email, get_user_by_id, get_user_by_username, update_google_user
from sqlalchemy.orm import Session
from app.db.db_connection import get_db
from app.models import User
from app.crud.refresh_token import create_refresh_token_in_db, get_valid_refresh_token, revoke_all_refresh_tokens
from google.oauth2 import id_token 
from google.auth.transport import requests as google_request


ACCESS_TOKEN_EXPIRE_MINUTES = 2


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login-with-docs")

# Function to create a new access token 
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_settings().jwt_secret_key, algorithm=get_settings().jwt_algorithm)
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

def verify_google_token(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1] 

        id_info = id_token.verify_oauth2_token(
            token, 
            google_request.Request(), 
            get_settings().web_client_id
        )

        # Verify the token is issued by Google
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Invalid issuer')

        return {"sub": id_info.get("sub"), "email": id_info.get("email"),}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Function to decode the JWT token and extract the user information
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_settings().jwt_secret_key, algorithms=[get_settings().jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    return user

# Function to authenticate the user using username or email and password
def authenticate_user(db: Session, userid: str, password: str) -> AuthResponse:
    user = None
    if '@' in userid:
        user = get_user_by_email(db, userid)
    else:
        user = get_user_by_username(db, userid)

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="User not verified")
    
    access_token = create_access_token(data={"sub": str(user.id)},)
    refresh_token = create_refresh_token(user.id, db)

    return AuthResponse(
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        ),
        user=user
    )


def authenticate_google_user(db: Session, email: str, sub: str) -> AuthResponse:
    db_user = get_user_by_email(db, email)

    if db_user is None:
        db_user = create_google_user(db, email, sub)
    else:
        # If the user exists but doesn't have a sub, update the user with the new sub
        if db_user.sub is None:
            db_user = update_google_user(db, db_user, sub)
            
    # Generate tokens for the user
    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(db_user.id, db)

    return AuthResponse(
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        ),
        user= db_user
    )

# Function to refresh the access token using a valid refresh token
def refresh_user_token(db: Session, refresh_token: str) -> TokenResponse:
    db_token = get_valid_refresh_token(db, refresh_token)
    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    user = get_user_by_id(db, db_token.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    revoke_all_refresh_tokens(db, user.id)

    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(user.id, db)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )
    


