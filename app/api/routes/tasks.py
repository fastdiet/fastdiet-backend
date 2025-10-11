import logging
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.db_connection import get_sync_session
from app.core.config import get_settings
from app.services.user import delete_unverified_users

router = APIRouter(prefix="/tasks", tags=["Tasks"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/delete-unverified-users", summary="Deletes users that have not verified their account")
async def trigger_delete_unverified_users(
    x_task_auth: str | None = Header(None, alias="X-Task-Auth-Key"), 
    db: Session = Depends(get_sync_session)
):
    if not settings.task_secret_key or x_task_auth != settings.task_secret_key:
        logger.warning("Unauthorized attempt to run a task.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    result = delete_unverified_users(db)
    logger.info(f"Task delete_unverified_users executed: {result}")
    return result