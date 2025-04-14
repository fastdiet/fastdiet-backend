from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class IngredientsProduct(Base):
    __tablename__ = 'ingredients_products'
    
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    
    # Relationships
    ingredient = relationship("Ingredient", back_populates="ingredients_products")
    product = relationship("Product", back_populates="ingredients_products")