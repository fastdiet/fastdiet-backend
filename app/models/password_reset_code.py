from app.db.db_connection import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, func, TIMESTAMP
from sqlalchemy.orm import relationship

class PasswordResetCode(Base):
    __tablename__ = 'password_reset_codes'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(8), nullable=False, index=True)
    expires_at = Column(TIMESTAMP, nullable=False, default=func.now())
    used = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())

    user = relationship('User', back_populates="password_reset_codes")