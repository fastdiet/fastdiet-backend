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
    date = Column(TIMESTAMP, nullable=False)
    day = Column(String (50), nullable=False)
    slot = Column(Integer, nullable=False) 
    position = Column(Integer, nullable=False)
    meal_plan_id = Column(Integer, ForeignKey('meal_plans.id', ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, nullable=False)
    item_type = Column(Enum(MealItemType), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    meal_plan = relationship("MealPlan", back_populates="meals")