from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class Intolerance(Base):
    __tablename__ = 'intolerances'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    
    # Relationships
    user_preferences_intolerances = relationship("UserPreferencesIntolerance", back_populates="intolerance")