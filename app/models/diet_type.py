from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class DietType(Base):
    __tablename__ = 'diet_types'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    
    # Relationships
    user_preferences = relationship("UserPreferences", back_populates="diet_type")
    recipes = relationship("Recipe", secondary="recipes_diet_types", back_populates="diet_types")