from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class RecipesNutrient(Base):
    __tablename__ = 'recipes_nutrients'
    
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete="CASCADE"), primary_key=True)
    nutrient_id = Column(Integer, ForeignKey('nutrients.id'), primary_key=True)
    amount = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="recipes_nutrients")
    nutrient = relationship("Nutrient", back_populates="recipes_nutrients")