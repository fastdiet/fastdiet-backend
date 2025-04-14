from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class RecipesDietType(Base):
    __tablename__ = 'recipes_diet_types'
    
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete="CASCADE"), primary_key=True)
    diet_type_id = Column(Integer, ForeignKey('diet_types.id'), primary_key=True)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="recipes_diet_types")
    diet_type = relationship("DietType", back_populates="recipes_diet_types")