from sqlalchemy import Column, Integer, ForeignKey

from app.db.db_connection import Base

class UserPreferencesIntolerance(Base):
    __tablename__ = 'user_preferences_intolerances'
    
    preference_id = Column(Integer, ForeignKey('user_preferences.id', ondelete="CASCADE"), primary_key=True)
    intolerance_id = Column(Integer, ForeignKey('intolerances.id'), primary_key=True)