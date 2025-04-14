from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class UserPreferencesIntolerance(Base):
    __tablename__ = 'user_preferences_intolerances'
    
    preference_id = Column(Integer, ForeignKey('user_preferences.id', ondelete="CASCADE"), primary_key=True)
    intolerance_id = Column(Integer, ForeignKey('intolerances.id'), primary_key=True)
    
    # Relationships
    user_preference = relationship("UserPreferences", back_populates="user_preferences_intolerances")
    intolerance = relationship("Intolerance", back_populates="user_preferences_intolerances")