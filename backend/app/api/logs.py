from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.repository import Repository
from app.schemas.agent import LogListResponse, LogEntrySchema

router = APIRouter(prefix="/api/logs", tags=["System Logs"])


@router.get("", response_model=LogListResponse)
def get_logs(
    level: Optional[str] = Query(default=None, description="INFO, WARNING, ERROR, or ALL"),
    search: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Query recent structured logs stored in database."""
    repo = Repository(db)
    total, logs = repo.list_logs(
        level=level,
        search=search,
        skip=skip,
        limit=limit,
    )
    schemas = [
        LogEntrySchema(
            id=log.id,
            level=log.level,
            message=log.message,
            details=log.details,
            created_at=log.created_at,
        )
        for log in logs
    ]
    return LogListResponse(total=total, logs=schemas)


@router.delete("")
def clear_logs(db: Session = Depends(get_db)):
    """Clear all stored log entries."""
    repo = Repository(db)
    repo.clear_logs()
    return {"success": True, "message": "Logs cleared"}
