from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class CuisineRegion(Base):
    __tablename__ = 'cuisine_regions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    
    # Relationships
    user_preferences_cuisines = relationship("UserPreferencesCuisine", back_populates="cuisine")
    recipes_cuisines = relationship("RecipesCuisine", back_populates="cuisine")