from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class RecipesDishType(Base):
    __tablename__ = 'recipes_dish_types'
    
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete="CASCADE"), primary_key=True)
    dish_type_id = Column(Integer, ForeignKey('dish_types.id'), primary_key=True)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="recipes_dish_types")
    dish_type = relationship("DishType", back_populates="recipes_dish_types")