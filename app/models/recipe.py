from sqlalchemy import JSON, TIMESTAMP, Column, ForeignKey, Integer, String, Boolean, Float, Text, func
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class Recipe(Base):
    __tablename__ = 'recipes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    spoonacular_id = Column(Integer, nullable=True, unique=True)
    title = Column(String(255), nullable=False)
    title_es = Column(String(255), nullable=True)
    creator_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=True)
    image_url = Column(String(255), nullable=True)
    image_type = Column(String(50), nullable=True)

    ready_min = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    summary_es = Column(Text, nullable=True)


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
    analyzed_instructions_es = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    
    cuisines = relationship("CuisineRegion", secondary="recipes_cuisines", back_populates="recipes", passive_deletes=True)
    dish_types = relationship("DishType", secondary="recipes_dish_types", back_populates="recipes", passive_deletes=True)
    diet_types = relationship("DietType", secondary="recipes_diet_types", back_populates="recipes", passive_deletes=True)
    recipes_nutrients = relationship("RecipesNutrient", back_populates="recipe", cascade="all, delete-orphan", passive_deletes=True)
    recipes_ingredients = relationship("RecipesIngredient", back_populates="recipe", cascade="all, delete-orphan",passive_deletes=True)
    meal_items = relationship("MealItem", back_populates="recipe", cascade="all, delete-orphan", passive_deletes=True)
    creator = relationship("User", back_populates="created_recipes")