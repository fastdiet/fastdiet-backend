from datetime import datetime, timedelta
import logging
import secrets
from fastapi import  Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
import requests
from app.core.errors import ErrorCode
from app.core.security import verify_password
from app.crud.user_preferences import get_user_preferences_by_user_id, get_user_preferences_details
from app.schemas.token import AuthResponse, TokenResponse
from jose import JWTError, jwt
from app.core.config import get_settings
from app.crud.user import create_apple_user, create_google_user, get_user_by_email, get_user_by_id, get_user_by_username, update_apple_user, update_google_user
from sqlalchemy.orm import Session
from app.db.db_connection import get_db
from app.models import User
from app.crud.refresh_token import create_refresh_token_in_db, get_valid_refresh_token, revoke_all_refresh_tokens
from google.oauth2 import id_token 
from google.auth.transport import requests as google_request


ACCESS_TOKEN_EXPIRE_MINUTES = 30

APPLE_PUBLIC_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_AUDIENCE = "com.fastdiet.app"
APPLE_ISSUER = "https://appleid.apple.com"

logger = logging.getLogger(__name__)
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
        if not authorization.startswith("Bearer "):
            raise ValueError("Authorization header must start with 'Bearer '")
        
        token = authorization.split(" ")[1] 
        if not token:
            raise ValueError("Token cannot be empty")

        id_info = id_token.verify_oauth2_token(
            token, 
            google_request.Request(), 
        )

        # Verify the token is issued by Google
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            logger.warning(f"Invalid Google token issuer: {id_info['iss']}")
            raise ValueError('Invalid issuer')

        logger.info(f"Successfully verified Google token for email: {id_info.get('email')}")
        return {"sub": id_info.get("sub"), "email": id_info.get("email"),}

    except ValueError as e:
        logger.warning(f"Google token verification failed: {e}")
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.INVALID_GOOGLE_TOKEN, "message": "Invalid Google token"}
        )
    except Exception as e:
        logger.error("An unexpected error occurred during Google token verification.", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.INVALID_GOOGLE_TOKEN, "message": "Could not verify Google token"}
        )
    

def verify_apple_token(authorization: str = Header(...)):
    try:
        if not authorization.startswith("Bearer "):
            raise ValueError("Authorization header must start with 'Bearer '")
        
        token = authorization.split(" ")[1] 
        if not token:
            raise ValueError("Token cannot be empty")

    
        apple_keys = requests.get(APPLE_PUBLIC_KEYS_URL).json()["keys"]

        header = jwt.get_unverified_header(token)
        key = next((k for k in apple_keys if k["kid"] == header["kid"]), None)
        if not key:
            raise ValueError("Invalid key ID")

        public_key = jwt.construct_rsa_public_key(key)
        decoded = jwt.decode(
            token,
            public_key,
            audience=APPLE_AUDIENCE,
            issuer=APPLE_ISSUER,
            options={"verify_exp": True}
        )

        email = decoded.get("email")
        sub = decoded.get("sub")

        if not sub:
            raise ValueError("Missing Apple sub claim")

        logger.info(f"Verified Apple token for {email or 'unknown email'}")
        return {"sub": sub, "email": email}

    except Exception as e:
        logger.warning(f"Apple token verification failed: {e}")
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.INVALID_APPLE_TOKEN, "message": "Invalid Apple token"}
        )

# Function to decode the JWT token and extract the user information
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail={"code": ErrorCode.INVALID_CREDENTIALS, "message": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_settings().jwt_secret_key, algorithms=[get_settings().jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("JWT token is valid but 'sub' (user ID) claim is missing.")
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_id(db, int(user_id))
    if user is None:
        logger.error(f"Token is valid for user ID {user_id}, but this user was not found in the database.")
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
        logger.warning(f"Failed login for '{userid}': Incorrect username or password.")
        raise HTTPException(
            status_code=401,
            detail={"code": ErrorCode.INVALID_CREDENTIALS, "message": "Incorrect username or password"}
        )
    if not user.is_verified:
        logger.warning(f"Failed login for user ID {user.id} ({userid}): Account is not verified.")
        raise HTTPException(
            status_code=403,
            detail={"code": ErrorCode.USER_NOT_VERIFIED, "message": "User not verified"}
        )
    
    logger.info(f"User ID {user.id} ({user.username}) authenticated successfully. Creating tokens.")
    access_token = create_access_token(data={"sub": str(user.id)},)
    refresh_token = create_refresh_token(user.id, db)

    preferences = get_user_preferences_details(db, user.id)

    return AuthResponse(
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        ),
        user=user,
        preferences=preferences
    )


def authenticate_google_user(db: Session, email: str, sub: str) -> AuthResponse:
    db_user = get_user_by_email(db, email)

    if db_user is None:
        logger.info(f"No existing user found for email '{email}'. Creating a new user from Google sign-in.")
        db_user = create_google_user(db, email, sub)
        logger.info(f"New user created via Google with ID: {db_user.id}")
    else:
        logger.info(f"Existing user ID {db_user.id} ({db_user.username}) authenticated via Google.")
        # If the user exists but doesn't have a sub, update the user with the new sub
        if db_user.sub is None:
            db_user = update_google_user(db, db_user, sub)
            
    # Generate tokens for the user
    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(db_user.id, db)
    preferences = get_user_preferences_details(db, db_user.id)

    return AuthResponse(
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        ),
        user= db_user,
        preferences=preferences
    )

def authenticate_apple_user(db: Session, email: str | None, sub: str) -> AuthResponse:
    db_user = None
    if email:
        db_user = get_user_by_email(db, email)
    
    if db_user is None:
        logger.info(f"No user found for {email or 'unknown email'}. Creating Apple user.")
        db_user = create_apple_user(db, email, sub)
    else:
        if db_user.sub is None:
            db_user = update_apple_user(db, db_user, sub)

    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(db_user.id, db)
    preferences = get_user_preferences_details(db, db_user.id)

    return AuthResponse(
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        ),
        user=db_user,
        preferences=preferences
    )

# Function to refresh the access token using a valid refresh token
def refresh_user_token(db: Session, refresh_token: str) -> TokenResponse:
    db_token = get_valid_refresh_token(db, refresh_token)
    if not db_token:
        logger.warning("Token refresh failed: Invalid or expired refresh token provided.")
        raise HTTPException(
            status_code=401,
            detail={"code": ErrorCode.INVALID_OR_EXPIRED_REFRESH_TOKEN, "message": "Invalid or expired refresh token"}
        )
    
    user = get_user_by_id(db, db_token.user_id)
    if not user:
        logger.error(f"Refresh token is valid for user ID {db_token.user_id}, but user not found in DB.")
        raise HTTPException(
            status_code=401,
            detail={"code": ErrorCode.INVALID_TOKEN, "message": "Invalid token"}
        )
    
    revoke_all_refresh_tokens(db, user.id)

    logger.info(f"Access token refreshed for user ID: {user.id} ({user.username}).")
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(user.id, db)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )

def get_language(accept_language: str = Header(default="en")) -> str:
    """ Dependency to get the requested language from the 'accept-language' header"""
    if "es" in accept_language.lower():
        return "es"
    return "en"

    


