import enum
from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, ForeignKey, Enum, func
from sqlalchemy.orm import relationship

from app.db.db_connection import Base

class FeedbackType(enum.Enum):
    suggestion = "suggestion"
    bug = "bug"
    other = "other"

class FeedbackStatus(enum.Enum):
    new = "new"
    in_progress = "in_progress"
    resolved = "resolved"
    wont_fix = "wont_fix"

class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    feedback_type = Column(Enum(FeedbackType), nullable=False)
    message = Column(Text, nullable=False)
    
    app_version = Column(String(50), nullable=True)
    platform = Column(String(20), nullable=True)
    platform_version = Column(String(50), nullable=True)

    status = Column(Enum(FeedbackStatus), nullable=False, default=FeedbackStatus.new)
    created_at = Column(TIMESTAMP, default=func.now())
    
    # Relationship to User
    user = relationship("User", back_populates="feedback")