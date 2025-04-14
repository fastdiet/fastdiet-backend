from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class Ingredient(Base):
    __tablename__ = 'ingredients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    image_url = Column(String(255), nullable=True)
    
    # Relationships
    ingredients_products = relationship("IngredientsProduct", back_populates="ingredient")