import enum
from sqlalchemy import Column, Integer, ForeignKey, String, TIMESTAMP, func, Enum
from sqlalchemy.orm import relationship
from app.db.db_connection import Base

class MealItemType(enum.Enum):
    RECIPE = "RECIPE"
    PRODUCT = "PRODUCT"
    INGREDIENT = "INGREDIENT"
    MENU_ITEM = "MENU_ITEM"
    CUSTOM_FOOD = "CUSTOM_FOOD"

class MealItem(Base):
    __tablename__ = 'meal_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    day = Column(Integer, nullable=False)
    slot = Column(Integer, nullable=False)
    meal_plan_id = Column(Integer, ForeignKey('meal_plans.id', ondelete="CASCADE"), nullable=False)
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    meal_plan = relationship("MealPlan", back_populates="meal_items")
    recipe = relationship("Recipe", back_populates="meal_items")
