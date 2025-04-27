from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.db.db_connection import get_db
from app.core.auth import authenticate_user, get_current_user, refresh_user_token
from app.schemas.token import AuthResponse, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.schemas.common import SuccessResponse
from app.schemas.email_verification_code import EmailCode
from app.crud.user import get_user_by_email
from app.models.user import User
from app.services.email_verification_code import create_and_send_verification_code, verify_user_email
from app.schemas.reset_password import ResetPasswordRequest
from app.services.user import register_user
from app.crud.refresh_token import revoke_all_refresh_tokens
from app.core.rate_limiter import limiter
from app.services.password import create_and_send_reset_code, reset_user_password, verify_valid_reset_code


router = APIRouter(tags=["auth"])

@router.post("/login", response_model=AuthResponse)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Endpoint to login a user and return access and refresh tokens"""
    return authenticate_user(db, form_data.username, form_data.password)

@router.post("/logout", response_model=SuccessResponse)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Endpoint to revoke all refresh tokens of the user"""
    revoke_all_refresh_tokens(db, current_user.id)
    return SuccessResponse(success=True, message="Logged out successfully")

@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("3/minute")
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """Endpoint to register a new user"""
    user_data.email = user_data.email.strip().lower()
    if user_data.username:
        user_data.username = user_data.username.strip().lower() 
    user = register_user(db, user_data)
    return user

@router.post("/send-verification-code", response_model=SuccessResponse)
@limiter.limit("1/minute")
def send_verification_code(request: Request, email: EmailStr, db: Session = Depends(get_db)):
    """Endpoint to send a verification code to the user's email"""
    email = email.strip().lower()
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="User already verified")

    create_and_send_verification_code(user, db)
    return SuccessResponse(success=True, message="Verification code sent.")

@router.post("/verify-email", response_model=SuccessResponse)
def verify_email(data: EmailCode, db: Session = Depends(get_db)):
    """Endpoint to verify the user's email using a verification code"""
    email = data.email.strip().lower()
    verify_user_email(db, email, data.code)
    return SuccessResponse(success=True, message="Email verified successfully")


@router.post("/refresh-token", response_model=TokenResponse)
@limiter.limit("10/minute")
def refresh_access_token(request: Request, refresh_token: str = Body(...), db: Session = Depends(get_db)):
    """Endpoint to refresh the access token using a refresh token"""
    return refresh_user_token(db, refresh_token)


@router.post("/send-reset-code", response_model=SuccessResponse)
@limiter.limit("1/minute")
def send_reset_code(request: Request, email: EmailStr, db: Session = Depends(get_db)):
    """Endpoint to send a password reset code to the user's email"""
    email = email.strip().lower()
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="You need to verify your email before resetting the password")
    
    create_and_send_reset_code(user, db)
    
    return SuccessResponse(success=True, message="Reset code sent successfully")

@router.post("/verify-reset-code", response_model=SuccessResponse)
@limiter.limit("5/minute")
def verify_reset_code(request: Request, data: EmailCode, db: Session = Depends(get_db)):
    """Endpoint to verify if a password reset code is valid"""
    email = data.email.strip().lower()
    verify_valid_reset_code(db, email, data.code)

    return SuccessResponse(success=True, message="Reset code is valid.")

@router.post("/reset-password", response_model=SuccessResponse)
@limiter.limit("3/minute")
def reset_password(request: Request, data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Endpoint to reset the password using a valid reset code"""
    email = data.email.strip().lower()
    reset_user_password(db, email, data.code, data.new_password)

    return SuccessResponse(success=True, message="Password has been reset successfully.")