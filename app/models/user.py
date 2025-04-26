from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, func, Enum
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sub = Column(String(255), unique=True, nullable=True)
    username = Column(String(40), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    name = Column(String(40), nullable=True)
    auth_method = Column(Enum('google', 'traditional', name='auth_method_types'), nullable=False, default="traditional")
    is_verified = Column(Boolean, default=False)
    spoonacular_username = Column(String(255), nullable=True)
    spoonacular_hash = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    # Relationships
    user_preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    meal_plans = relationship("MealPlan", back_populates="user")
    email_verification_codes = relationship("EmailVerificationCode", back_populates="user", cascade="all, delete-orphan")
    password_reset_codes = relationship("PasswordResetCode", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")