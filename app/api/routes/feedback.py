import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.db_connection import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate
from app.schemas.common import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"], prefix="/feedback")

@router.post(
    "/",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED
)
def submit_feedback(
    feedback_data: FeedbackCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """ Endpoint for users to submit feedback (suggestions, bugs, etc.)."""
    logger.info(f"User ID: {current_user.id} ({current_user.email}) is submitting feedback.")

    new_feedback = Feedback(
        user_id=current_user.id,
        feedback_type=feedback_data.feedback_type,
        message=feedback_data.message,
        app_version=feedback_data.app_version,
        platform=feedback_data.platform,
        platform_version=str(feedback_data.platform_version)
    )

    db.add(new_feedback)
    db.commit()

    logger.info(f"Feedback from User ID: {current_user.id} successfully saved with ID: {new_feedback.id}.")

    return SuccessResponse(success=True, message="Feedback submitted successfully")