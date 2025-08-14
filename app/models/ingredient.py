from sqlalchemy import JSON, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class Ingredient(Base):
    __tablename__ = 'ingredients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    spoonacular_id = Column(Integer, nullable=True, unique=True, index=True)
    name_en = Column(String(255), nullable=False, index=True, unique=True)
    name_es =Column(String(255), nullable=True, index=True)
    image_filename = Column(String(255), nullable=True)
    aisle = Column(String(100), nullable=True)
    possible_units_en = Column(JSON, nullable=True)
    possible_units_es = Column(JSON, nullable=True)
    
    ingredients_products = relationship("IngredientsProduct", back_populates="ingredient")
    recipes_ingredients = relationship("RecipesIngredient", back_populates="ingredient")