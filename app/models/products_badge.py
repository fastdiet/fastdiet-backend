from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class ProductsBadge(Base):
    __tablename__ = 'products_badges'
    
    product_id = Column(Integer, ForeignKey('products.id', ondelete="CASCADE"), primary_key=True)
    badge_id = Column(Integer, ForeignKey('badges.id'), primary_key=True)
    
    # Relationships
    product = relationship("Product", back_populates="products_badges")
    badge = relationship("Badge", back_populates="products_badges")