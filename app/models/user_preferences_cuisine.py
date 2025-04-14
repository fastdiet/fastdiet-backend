from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class UserPreferencesCuisine(Base):
    __tablename__ = 'user_preferences_cuisines'
    
    preference_id = Column(Integer, ForeignKey('user_preferences.id', ondelete="CASCADE"), primary_key=True)
    cuisine_id = Column(Integer, ForeignKey('cuisine_regions.id'), primary_key=True)
    
    # Relationships
    user_preference = relationship("UserPreferences", back_populates="user_preferences_cuisines")
    cuisine = relationship("CuisineRegion", back_populates="user_preferences_cuisines")