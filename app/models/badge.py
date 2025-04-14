from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class Badge(Base):
    __tablename__ = 'badges'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    is_important = Column(Boolean, default=False)
    
    # Relationships
    products_badges = relationship("ProductsBadge", back_populates="badge")