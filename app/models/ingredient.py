from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class Ingredient(Base):
    __tablename__ = 'ingredients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    spoonacular_id = Column(Integer, nullable=True, unique=True, index=True)
    name = Column(String(255), nullable=False, index=True, unique=True)
    image_filename = Column(String(255), nullable=True)
    aisle = Column(String(100), nullable=True)
    
    ingredients_products = relationship("IngredientsProduct", back_populates="ingredient")
    recipes_ingredients = relationship("RecipesIngredient", back_populates="ingredient")