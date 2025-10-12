from pydantic import BaseModel, Field
from app.models.feedback import FeedbackType

class FeedbackCreate(BaseModel):
    feedback_type: FeedbackType
    message: str = Field(..., min_length=10, max_length=1000)
    app_version: str
    platform: str
    platform_version: str | int