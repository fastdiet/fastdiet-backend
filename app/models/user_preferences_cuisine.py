from sqlalchemy import Column, Integer, ForeignKey

from app.db.db_connection import Base

class UserPreferencesCuisine(Base):
    __tablename__ = 'user_preferences_cuisines'
    
    preference_id = Column(Integer, ForeignKey('user_preferences.id', ondelete="CASCADE"), primary_key=True)
    cuisine_id = Column(Integer, ForeignKey('cuisine_regions.id'), primary_key=True)