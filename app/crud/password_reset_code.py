
from datetime import datetime
from app.models.password_reset_code import PasswordResetCode
from sqlalchemy.orm import Session


def get_valid_password_reset_code(db: Session, user_id: str, code: str) -> PasswordResetCode | None:
    return db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user_id,
        PasswordResetCode.code == code,
        PasswordResetCode.expires_at > datetime.utcnow(),
        PasswordResetCode.used == False
    ).first()


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