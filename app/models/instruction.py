from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class Instruction(Base):
    __tablename__ = 'instructions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    step_number = Column(Integer, nullable=False)
    step_text = Column(String(1000), nullable=False)
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete="CASCADE"), nullable=False)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="instructions")
    instructions_equipments = relationship("InstructionsEquipment", back_populates="instruction")