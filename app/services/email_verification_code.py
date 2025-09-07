from datetime import datetime, timedelta
import random
import string
from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.core.email_templates import EMAIL_TEXTS
from app.core.errors import ErrorCode
from app.models.user import User
from app.services.email import send_email
from fastapi import HTTPException
from app.crud.user import get_user_by_email
from app.crud.email_verification_code import create_email_verification_code, get_valid_email_verification_code, mark_old_verification_codes_as_used

# Function to generate a random confirmation code
def generate_confirmation_code(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))

# Function to create a new confirmation code and send it to the user's email
def create_and_send_verification_code(user: User, db: Session, lang: str):
    
    code = generate_confirmation_code()
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    mark_old_verification_codes_as_used(db, user.id)
    email_verification_code = create_email_verification_code(
        db=db,
        code=code,
        user_id=user.id,
        expires_at=expires_at
    )

    user_display = user.name or user.username or "user"

    lang_texts = EMAIL_TEXTS.get(lang, EMAIL_TEXTS["en"])
    action_texts = lang_texts["verification"]

    email_context = {
        "title": action_texts["title"],
        "greeting": action_texts["greeting"],
        "user_display": user_display,
        "line1": action_texts["line1"],
        "code": email_verification_code.code,
        "line2": action_texts["line2"],
        "farewell": action_texts["farewell"],
        "footer_text": lang_texts["footer_text"]
    }

    send_email(
        to_email=user.email,
        subject=action_texts["subject"],
        template_context=email_context
    )

# Function to verify the user's email using the confirmation code
def verify_user_email(db: Session, email: EmailStr, code: str) -> None:
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.USER_NOT_FOUND, "message": "User not found"}
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.EMAIL_ALREADY_VERIFIED, "message": "Email already verified"}
        )

    confirmation = get_valid_email_verification_code(db, user.id, code)

    if not confirmation:
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.INVALID_EMAIL_VERIFICATION_CODE, "message": "Invalid or expired code"}
        )

    confirmation.used = True
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user