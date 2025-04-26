from app.models.email_verification_code import EmailVerificationCode
from datetime import datetime
from sqlalchemy.orm import Session

# Function to get a valid email verification code for a user
def get_valid_email_verification_code(db : Session, user_id: int, code: str) -> EmailVerificationCode | None:
    return db.query(EmailVerificationCode).filter(
        EmailVerificationCode.user_id == user_id,
        EmailVerificationCode.code == code,
        EmailVerificationCode.expires_at > datetime.utcnow(),
        EmailVerificationCode.used == False
    ).first()

# Function to create a new email verification code
def create_email_verification_code(db: Session, code: str, user_id: int, expires_at: datetime) -> EmailVerificationCode:
    db_verification_code = EmailVerificationCode(
        code=code,
        user_id=user_id,
        used=False,
        expires_at=expires_at
    )
    db.add(db_verification_code)
    db.commit()
    db.refresh(db_verification_code)
    return db_verification_code

# Function to mark old verification codes as used
def mark_old_verification_codes_as_used(db: Session, user_id: int):
    db.query(EmailVerificationCode).filter(
        EmailVerificationCode.user_id == user_id,
        EmailVerificationCode.used == False,
        EmailVerificationCode.expires_at > datetime.utcnow()
    ).update({EmailVerificationCode.used: True})
    db.commit()
