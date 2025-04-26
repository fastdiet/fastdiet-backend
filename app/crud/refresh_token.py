
from datetime import datetime
from app.models.refresh_token import RefreshToken
from sqlalchemy.orm import Session

# Function to get a valid refresh token for a user
def get_valid_refresh_token(db: Session, token: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.expires_at > datetime.utcnow(),
        RefreshToken.is_revoked == False
    ).first()

# Function to create a new refresh token
def create_refresh_token_in_db(db: Session, token: str, user_id: int, expires_at: datetime) -> RefreshToken:
    db_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

# Function to mark old refresh tokens as revoked
def revoke_all_refresh_tokens(db: Session, user_id: int):
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).update({RefreshToken.is_revoked: True})
    db.commit()
