from datetime import datetime, timedelta
from fastapi import HTTPException
from app.models.user import User
from app.models.password_reset_code import PasswordResetCode
from app.services.email import send_email
from app.services.email_verification_code import generate_confirmation_code
from app.crud.password_reset_code import create_password_reset_code, get_valid_password_reset_code, mark_old_reset_codes_as_used
from app.crud.user import get_user_by_email
from sqlalchemy.orm import Session
from app.core.security import hash_password


def create_and_send_reset_code(user: User, db: Session):
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

    send_email(
        to_email=user.email,
        subject="Your password reset code",
        body=f"Hi {user_display},\n\nYour password reset code is: {password_reset_code.code}\nIt will expire in 15 minutes."
    )

def verify_valid_reset_code(db: Session, email: str, code: str) -> tuple[User, PasswordResetCode]:
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_code = get_valid_password_reset_code(db, user.id, code)
    if not reset_code:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    
    return user, reset_code
    
def reset_user_password(db: Session, email: str, code: str, new_password: str):
    user, reset_code = verify_valid_reset_code(db, email, code)

    user.hashed_password = hash_password(new_password)
    reset_code.used = True

    db.commit()