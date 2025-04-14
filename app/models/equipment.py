from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class Equipment(Base):
    __tablename__ = 'equipments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    image_url = Column(String(255), nullable=True)
    
    # Relationships
    instructions_equipments = relationship("InstructionsEquipment", back_populates="equipment")