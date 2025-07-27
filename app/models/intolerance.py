from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class Intolerance(Base):
    __tablename__ = 'intolerances'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    
    # Relationships
    user_preferences = relationship("UserPreferences", secondary="user_preferences_intolerances", back_populates="intolerances")