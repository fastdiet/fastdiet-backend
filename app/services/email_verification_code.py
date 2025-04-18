from datetime import datetime, timedelta
import random
import string
from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.models.email_verification_code import EmailVerificationCode
from app.models.user import User
from app.services.email import send_email
from fastapi import HTTPException
from app.crud.user import get_user_by_email
from app.crud.email_verification_code import can_send_code, create_email_verification_code, get_valid_email_verification_code, mark_old_verification_codes_as_used

# Function to generate a random confirmation code
def generate_confirmation_code(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))

# Function to create a new confirmation code and send it to the user's email
def create_and_send_code(user: User, db: Session):
    if not can_send_code(db, user.id):
        raise HTTPException(status_code=429, detail="Please wait 2 minutes before requesting another code.")
    
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

    send_email(
        to_email=user.email,
        subject="Your confirmation code",
        body=f"Hi {user_display},\n\nYour confirmation code is: {email_verification_code.code}\nIt will expire in 15 minutes."
    )

# Function to verify the user's email using the confirmation code
def verify_user_email(db: Session, email: EmailStr, code: str) -> None:
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    confirmation = get_valid_email_verification_code(db, user.id, code)

    if not confirmation:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    confirmation.used = True
    user.is_verified = True
    db.commit()
    db.refresh(user)