from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class Nutrient(Base):
    __tablename__ = 'nutrients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False)
    
    # Relationships
    products_nutrients = relationship("ProductsNutrient", back_populates="nutrient")
    recipes_nutrients = relationship("RecipesNutrient", back_populates="nutrient")