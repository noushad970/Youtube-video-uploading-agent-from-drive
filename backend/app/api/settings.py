from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.repository import Repository
from app.schemas.settings import AgentSettingsSchema, AgentSettingsUpdate
from app.services.scheduler_service import SchedulerService

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=AgentSettingsSchema)
def get_settings(db: Session = Depends(get_db)):
    """Retrieve current agent configuration settings."""
    repo = Repository(db)
    return repo.get_settings()


@router.put("", response_model=AgentSettingsSchema)
def update_settings(
    update_data: AgentSettingsUpdate,
    db: Session = Depends(get_db),
):
    """Update agent configuration settings."""
    repo = Repository(db)
    data = update_data.model_dump(exclude_unset=True)
    updated = repo.update_settings(**data)

    # If enabled or interval changed, update scheduler
    if "interval_minutes" in data or "enabled" in data:
        if updated.enabled:
            SchedulerService.reschedule(updated.interval_minutes)
        else:
            SchedulerService.pause_job()

    return updated
