from datetime import datetime, timedelta
from fastapi import HTTPException
from app.core.email_templates import EMAIL_TEXTS
from app.core.errors import ErrorCode
from app.models.user import User
from app.models.password_reset_code import PasswordResetCode
from app.services.email import send_email
from app.services.email_verification_code import generate_confirmation_code
from app.crud.password_reset_code import create_password_reset_code, get_valid_password_reset_code, mark_old_reset_codes_as_used
from app.crud.user import get_user_by_email
from sqlalchemy.orm import Session
from app.core.security import hash_password


def create_and_send_reset_code(user: User, db: Session, lang: str):
    code = generate_confirmation_code()
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    mark_old_reset_codes_as_used(db, user.id)
    password_reset_code = create_password_reset_code(
        db=db,
        code=code,
        user_id=user.id,
        expires_at=expires_at
    )

    user_display = user.name or user.username or "user"

    lang_texts = EMAIL_TEXTS.get(lang, EMAIL_TEXTS["en"])
    action_texts = lang_texts["password_reset"]

    email_context = {
        "title": action_texts["title"],
        "greeting": action_texts["greeting"],
        "user_display": user_display,
        "line1": action_texts["line1"],
        "code": password_reset_code.code,
        "line2": action_texts["line2"],
        "farewell": action_texts["farewell"],
        "footer_text": lang_texts["footer_text"]
    }

    send_email(
        to_email=user.email,
        subject=action_texts["subject"],
        template_context=email_context
    )

def verify_valid_reset_code(db: Session, email: str, code: str) -> tuple[User, PasswordResetCode]:
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"code": ErrorCode.USER_NOT_FOUND, "message": "User not found"}
        )

    reset_code = get_valid_password_reset_code(db, user.id, code)
    if not reset_code:
        raise HTTPException(
            status_code=400,
            detail={"code": ErrorCode.INVALID_RESET_CODE, "message": "Invalid or expired reset code"}
        )
    
    return user, reset_code
    
def reset_user_password(db: Session, email: str, code: str, new_password: str):
    user, reset_code = verify_valid_reset_code(db, email, code)

    user.hashed_password = hash_password(new_password)
    reset_code.used = True

    db.commit()