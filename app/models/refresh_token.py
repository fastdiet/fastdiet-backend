from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.db_connection import Base

class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(512), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=func.now())
    expires_at = Column(TIMESTAMP, default=func.now())

    user = relationship("User", back_populates="refresh_tokens")