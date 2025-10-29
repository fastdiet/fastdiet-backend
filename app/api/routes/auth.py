import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.errors import ErrorCode
from app.db.db_connection import get_db
from app.core.auth import authenticate_apple_user, authenticate_google_user, authenticate_user, get_current_user, get_language, refresh_user_token, verify_apple_token, verify_google_token
from app.schemas.token import AuthResponse, RefreshRequest, TokenResponse
from app.schemas.user import EmailRequest, UserRegister, UserResponse
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
from app.core.auth import create_access_token, create_refresh_token


logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Endpoint to login a user and return access and refresh tokens"""
    logger.info(f"Login attempt for user: {form_data.username}")
    return authenticate_user(db, form_data.username, form_data.password)

@router.post("/login-with-docs", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    auth_response = authenticate_user(db, form_data.username, form_data.password)

    return auth_response.tokens

@router.post("/login-with-google", response_model=AuthResponse)
def login_with_google(db: Session = Depends(get_db), id_info: dict = Depends(verify_google_token)):
    logger.info(f"Google sign-in attempt for email: {id_info.get('email')}")
    return authenticate_google_user(db, id_info["email"], id_info["sub"])

@router.post("/login-with-apple", response_model=AuthResponse)
def login_with_apple(db: Session = Depends(get_db), id_info: dict = Depends(verify_apple_token)):
    logger.info(f"Apple sign-in attempt for email: {id_info.get('email')}")
    return authenticate_apple_user(db, id_info["email"], id_info["sub"])


@router.post("/logout", response_model=SuccessResponse)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Endpoint to revoke all refresh tokens of the user"""
    logger.info(f"User ID: {current_user.id} ({current_user.username}) is logging out.")
    revoke_all_refresh_tokens(db, current_user.id)
    return SuccessResponse(success=True, message="Logged out successfully")

@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/minute")
def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    """Endpoint to register a new user"""
    email = user_data.email.strip().lower()
    logger.info(f"Traditional Registration attempt for email: {email}")
    user_data.email = email
    user = register_user(db, user_data)
    return user

@router.post("/send-verification-code", response_model=SuccessResponse)
@limiter.limit("2/minute")
async def send_verification_code(request: Request, email_request: EmailRequest, db: Session = Depends(get_db), lang: str = Depends(get_language)):
    """Endpoint to send a verification code to the user's email"""
    email = email_request.email.strip().lower()
    logger.info(f"Request to send verification code to email: {email}")

    user = get_user_by_email(db, email)
    if not user:
        logger.warning(f"Verification code request failed: User with email '{email}' not found.")
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.USER_NOT_FOUND, "message": "User not found"}
        )

    if user.is_verified:
        logger.warning(f"Verification code request failed for user ID {user.id} ({user.username}): User already verified.")
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.USER_ALREADY_VERIFIED, "message": "User already verified"}
        )

    await create_and_send_verification_code(user, db, lang)
    return SuccessResponse(success=True, message="Verification code sent")

@router.post("/verify-email", response_model=AuthResponse)
def verify_email(data: EmailCode, db: Session = Depends(get_db)):
    """Endpoint to verify the user's email using a verification code"""
    email = data.email.strip().lower()
    logger.info(f"Email verification attempt for: {email}")

    user = verify_user_email(db, email, data.code)
    logger.info(f"Email for user ID {user.id} verified successfully. Generating tokens.")
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(user.id, db)

    return AuthResponse(
        tokens=TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer"),
        user=user
    ) 


@router.post("/refresh-token", response_model=TokenResponse)
@limiter.limit("20/hour")
def refresh_access_token(request: Request, refresh_request: RefreshRequest, db: Session = Depends(get_db)):
    """Endpoint to refresh the access token using a refresh token"""
    logger.info("Access token refresh requested.")
    return refresh_user_token(db, refresh_request.refresh_token)


@router.post("/send-reset-code", response_model=SuccessResponse)
@limiter.limit("2/minute")
async def send_reset_code(request: Request, email_request: EmailRequest, db: Session = Depends(get_db), lang: str = Depends(get_language)):
    """Endpoint to send a password reset code to the user's email"""
    email = email_request.email.strip().lower()
    logger.info(f"Password reset code requested for email: {email}")
    user = get_user_by_email(db, email)
    if not user:
        logger.warning(f"Password reset request failed: User with email '{email}' not found.")
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.USER_NOT_FOUND, "message": "User not found"}
        )
    if not user.is_verified:
        logger.warning(f"Password reset request failed for user ID {user.id} ({user.username}): Email is not verified.")
        raise HTTPException(
            status_code=403,
            detail={"code": ErrorCode.USER_NOT_VERIFIED_FOR_RESET, "message": "You need to verify your email before resetting the password"}
        )
    
    await create_and_send_reset_code(user, db, lang)
    logger.info(f"Password reset code sent successfully to user ID: {user.id} ({user.username}).")

    return SuccessResponse(success=True, message="Reset code sent successfully")

@router.post("/verify-reset-code", response_model=SuccessResponse)
@limiter.limit("5/minute")
def verify_reset_code(request: Request, data: EmailCode, db: Session = Depends(get_db)):
    """Endpoint to verify if a password reset code is valid"""
    email = data.email.strip().lower()
    verify_valid_reset_code(db, email, data.code)

    return SuccessResponse(success=True, message="Reset code is valid")

@router.post("/reset-password", response_model=SuccessResponse)
@limiter.limit("5/minute")
def reset_password(request: Request, data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Endpoint to reset the password using a valid reset code"""
    email = data.email.strip().lower()
    logger.info(f"Password reset attempt for email: {email}")
    
    reset_user_password(db, email, data.code, data.new_password)

    logger.info(f"Password for user with email '{email}' has been reset successfully.")

    return SuccessResponse(success=True, message="Password has been reset successfully")

