from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.db_connection import Base

class RecipesIngredient(Base):
    __tablename__ = 'recipes_ingredients'

    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete="CASCADE"), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), primary_key=True)
    original_ingredient_name = Column(String(512), nullable=True) 
    
    amount = Column(Float, nullable=False)
    unit = Column(String(100), nullable=True)
    measures_json = Column(JSON, nullable=True)

    recipe = relationship("Recipe", back_populates="recipes_ingredients")
    ingredient = relationship("Ingredient", back_populates="recipes_ingredients")