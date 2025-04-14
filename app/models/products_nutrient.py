from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class ProductsNutrient(Base):
    __tablename__ = 'products_nutrients'
    
    product_id = Column(Integer, ForeignKey('products.id', ondelete="CASCADE"), primary_key=True)
    nutrient_id = Column(Integer, ForeignKey('nutrients.id'), primary_key=True)
    amount = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    
    # Relationships
    product = relationship("Product", back_populates="products_nutrients")
    nutrient = relationship("Nutrient", back_populates="products_nutrients")