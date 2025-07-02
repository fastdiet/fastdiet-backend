from sqlalchemy import JSON, Column, Integer, String, Boolean, Float, Text
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
    summary = Column(Text, nullable=True)


    vegetarian = Column(Boolean, nullable=True)
    vegan = Column(Boolean, nullable=True)
    gluten_free = Column(Boolean, nullable=True)
    dairy_free = Column(Boolean, nullable=True)
    very_healthy = Column(Boolean, nullable=True)
    cheap = Column(Boolean, nullable=True)
    very_popular = Column(Boolean, nullable=True)
    sustainable = Column(Boolean, nullable=True)
    low_fodmap = Column(Boolean, nullable=True)

    preparation_min = Column(Integer, nullable=True)
    cooking_min = Column(Integer, nullable=True)
    calories = Column(Float, nullable=True)

    analyzed_instructions = Column(JSON, nullable=True)
    
    
    recipes_cuisines = relationship("RecipesCuisine", back_populates="recipe", cascade="all, delete-orphan")
    recipes_dish_types = relationship("RecipesDishType", back_populates="recipe", cascade="all, delete-orphan")
    recipes_diet_types = relationship("RecipesDietType", back_populates="recipe", cascade="all, delete-orphan")
    recipes_nutrients = relationship("RecipesNutrient", back_populates="recipe", cascade="all, delete-orphan")
    recipes_ingredients = relationship("RecipesIngredient", back_populates="recipe", cascade="all, delete-orphan")
    meal_items = relationship("MealItem", back_populates="recipe")