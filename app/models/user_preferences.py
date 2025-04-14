from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class UserPreferences(Base):
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    diet_type_id = Column(Integer, ForeignKey('diet_types.id'), nullable=True)
    vegetarian = Column(Boolean, default=False)
    vegan = Column(Boolean, default=False)
    gluten_free = Column(Boolean, default=False)
    dairy_free = Column(Boolean, default=False)
    very_healthy = Column(Boolean, default=False)
    cheap = Column(Boolean, default=False)
    max_ready_min = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    calories_goal = Column(Float, nullable=True)
    sustainable = Column(Boolean, default=False)
    low_fodmap = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_preferences")
    diet_type = relationship("DietType", back_populates="user_preferences")
    user_preferences_cuisines = relationship("UserPreferencesCuisine", back_populates="user_preference")
    user_preferences_intolerances = relationship("UserPreferencesIntolerance", back_populates="user_preference")