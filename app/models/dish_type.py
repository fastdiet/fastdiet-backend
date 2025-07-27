from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class DishType(Base):
    __tablename__ = 'dish_types'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    
    # Relationships
    recipes = relationship("Recipe",secondary="recipes_dish_types", back_populates="dish_types")