from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class CuisineRegion(Base):
    __tablename__ = 'cuisine_regions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    
    # Relationships
    user_preferences = relationship("UserPreferences", secondary="user_preferences_cuisines", back_populates="cuisines")
    recipes = relationship("Recipe", secondary="recipes_cuisines", back_populates="cuisines")