
from app.models.password_reset_code import PasswordResetCode
from datetime import datetime
from sqlalchemy.orm import Session

# Function to get a valid password reset code for a user
def get_valid_password_reset_code(db : Session, user_id: int, code: str) -> PasswordResetCode | None:
    return db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user_id,
        PasswordResetCode.code == code,
        PasswordResetCode.expires_at > datetime.utcnow(),
        PasswordResetCode.used == False
    ).first()

# Function to create a new password reset code
def create_password_reset_code(db: Session, code: str, user_id: int, expires_at: datetime) -> PasswordResetCode:
    db_reset_code = PasswordResetCode(
        code=code,
        user_id=user_id,
        used=False,
        expires_at=expires_at
    )
    db.add(db_reset_code)
    db.commit()
    db.refresh(db_reset_code)
    return db_reset_code

# Function to mark old password reset codes as used
def mark_old_reset_codes_as_used(db: Session, user_id: int):
    db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user_id,
        PasswordResetCode.used == False,
        PasswordResetCode.expires_at > datetime.utcnow()
    ).update({PasswordResetCode.used: True})
    db.commit()
