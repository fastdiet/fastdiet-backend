from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    price = Column(Float, nullable=True)
    category = Column(String(255), nullable=True)
    calories = Column(Float, nullable=True)
    description = Column(String(1000), nullable=True)
    image_url = Column(String(255), nullable=True)
    image_type = Column(String(50), nullable=True)
    brand = Column(String(255), nullable=True)
    
    # Relationships
    ingredients_products = relationship("IngredientsProduct", back_populates="product")
    products_nutrients = relationship("ProductsNutrient", back_populates="product")
    products_badges = relationship("ProductsBadge", back_populates="product")