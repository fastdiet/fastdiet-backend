from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class RecipesCuisine(Base):
    __tablename__ = 'recipes_cuisines'
    
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete="CASCADE"), primary_key=True)
    cuisine_id = Column(Integer, ForeignKey('cuisine_regions.id'), primary_key=True)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="recipes_cuisines")
    cuisine = relationship("CuisineRegion", back_populates="recipes_cuisines")