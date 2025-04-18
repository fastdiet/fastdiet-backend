from datetime import datetime, timedelta
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.db.db_connection import get_db
from app.auth.auth import authenticate_user, get_current_user, refresh_user_token
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.schemas.common import SuccessResponse
from app.schemas.email_verification_code import EmailVerification
from app.crud.user import get_user_by_email
from app.models.user import User
from app.services.email_verification_code import create_and_send_code, generate_confirmation_code, verify_user_email
from app.services.email import send_email
from app.schemas.reset_password import ResetCodeVerification
from app.crud.password_reset_code import create_password_reset_code, get_valid_password_reset_code
from app.services.user import register_user
from app.crud.refresh_token import revoke_all_refresh_tokens


router = APIRouter(tags=["users"])

@router.post("/users/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Endpoint to login a user and return access and refresh tokens"""
    return authenticate_user(db, form_data.username, form_data.password)

@router.post("/users/logout", response_model=SuccessResponse)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Endpoint to revoke all refresh tokens of the user"""
    revoke_all_refresh_tokens(db, current_user.id)
    return SuccessResponse(success=True, message="Logged out successfully")

@router.post("/users/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Endpoint to register a new user"""
    user = register_user(db, user_data)
    return user

@router.post("/users/send-verification-code", response_model=SuccessResponse)
def send_verification_code(email: EmailStr, db: Session = Depends(get_db)):
    """Endpoint to send a verification code to the user's email"""
    email = email.strip().lower()
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="User already verified")

    create_and_send_code(user, db)
    return SuccessResponse(success=True, message="Verification code sent.")

@router.get("/users/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Endpoint to get the current user's profile"""
    return current_user

@router.post("/users/verify-email", response_model=SuccessResponse)
def verify_email(data: EmailVerification, db: Session = Depends(get_db)):
    """Endpoint to verify the user's email using a verification code"""
    email = data.email.strip().lower()
    verify_user_email(db, email, data.code)
    return SuccessResponse(success=True, message="Email verified successfully")


@router.post("/users/refresh-token", response_model=TokenResponse)
def refresh_access_token(refresh_token: str = Body(...), db: Session = Depends(get_db)):
    """Endpoint to refresh the access token using a refresh token"""
    return refresh_user_token(db, refresh_token)


@router.post("/users/forgot-password", response_model=SuccessResponse)
def forgot_password(email: EmailStr = Body(...), db: Session = Depends(get_db)):
    """Endpoint to send a password reset code to the user's email"""
    user = get_user_by_email(db, email)
    if not user:
        # For security reasons, we do not inform the user if the email is registered or not
        return SuccessResponse(success=True, message="If the email is registered, you will receive a password reset code")
    
    code = generate_confirmation_code()
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    reset_code = create_password_reset_code(
        user_id=user.id,
        code=code,
        expires_at=expires_at
    )

    send_email(
        to_email=user.email,
        subject="Password Reset Code",
        body=f"Hello {user.username},\n\nYour password reset code is: {reset_code.code}\nIt will expire in 1 hour."
    )
    
    return SuccessResponse(success=True, message="If the email is registered, you will receive a password reset code")

@router.post("/users/verify-reset-code", response_model=SuccessResponse)
def verify_reset_code(data: ResetCodeVerification, db: Session = Depends(get_db)):
    """Endpoint to verify the password reset code"""
    user = get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_code = get_valid_password_reset_code(
        db,
        user_id=user.id,
        code=data.code
    )
    
    if not reset_code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    return SuccessResponse(success=True, message="Code verified successfully")



