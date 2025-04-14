from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class InstructionsEquipment(Base):
    __tablename__ = 'instructions_equipments'
    
    instruction_id = Column(Integer, ForeignKey('instructions.id', ondelete="CASCADE"), primary_key=True)
    equipment_id = Column(Integer, ForeignKey('equipments.id'), primary_key=True)
    
    # Relationships
    instruction = relationship("Instruction", back_populates="instructions_equipments")
    equipment = relationship("Equipment", back_populates="instructions_equipments")