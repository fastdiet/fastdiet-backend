from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class Recipe(Base):
    __tablename__ = 'recipes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    spoonacular_id = Column(Integer, nullable=True, unique=True)
    title = Column(String(255), nullable=False)
    image_url = Column(String(255), nullable=True)
    image_type = Column(String(50), nullable=True)
    ready_min = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    vegetarian = Column(Boolean, default=False)
    vegan = Column(Boolean, default=False)
    gluten_free = Column(Boolean, default=False)
    dairy_free = Column(Boolean, default=False)
    very_healthy = Column(Boolean, default=False)
    cheap = Column(Boolean, default=False)
    very_popular = Column(Boolean, default=False)
    sustainable = Column(Boolean, default=False)
    low_fodmap = Column(Boolean, default=False)
    preparation_min = Column(Integer, nullable=True)
    cooking_min = Column(Integer, nullable=True)
    price_per_serving = Column(Float, nullable=True)
    summary = Column(String(255), nullable=True)
    
    # Relationships
    instructions = relationship("Instruction", back_populates="recipe")
    recipes_cuisines = relationship("RecipesCuisine", back_populates="recipe")
    recipes_dish_types = relationship("RecipesDishType", back_populates="recipe")
    recipes_diet_types = relationship("RecipesDietType", back_populates="recipe")
    recipes_nutrients = relationship("RecipesNutrient", back_populates="recipe")
    meal_items = relationship("MealItem", back_populates="recipe")