from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.repository import Repository
from app.services.google_auth_service import GoogleAuthService
from app.services.ai_service import AIService
from app.services.scheduler_service import SchedulerService
from app.schemas.agent import AgentStatusResponse, AgentRunResult

router = APIRouter(prefix="/api/agent", tags=["Agent Control"])


@router.get("/status", response_model=AgentStatusResponse)
def get_agent_status(db: Session = Depends(get_db)):
    """Get complete operational status of the YouTube AI Agent."""
    repo = Repository(db)
    settings = repo.get_settings()
    auth_service = GoogleAuthService(db)
    ai_service = AIService(db)

    auth_status = auth_service.get_auth_status()
    ai_health = ai_service.check_health()
    scheduler_status = SchedulerService.get_status()

    selected_folder = repo.get_selected_folder()
    folder_id = selected_folder.folder_id if selected_folder else None
    folder_name = selected_folder.folder_name if selected_folder else None

    stats = repo.get_video_stats(folder_id)
    latest_run = repo.get_latest_agent_run()

    # Get last successful upload timestamp
    _, latest_uploads = repo.list_uploads(status="uploaded", limit=1)
    last_upload_at = latest_uploads[0].uploaded_at if latest_uploads else None

    return AgentStatusResponse(
        is_running=settings.enabled,
        is_scheduler_running=scheduler_status["scheduler_running"],
        is_job_active=scheduler_status["is_job_currently_executing"],
        google_connected=auth_status["is_authenticated"],
        youtube_connected=auth_status["has_youtube_scope"],
        drive_connected=selected_folder is not None and auth_status["has_drive_scope"],
        ollama_connected=ai_health["connected"],
        selected_folder_name=folder_name,
        selected_folder_id=folder_id,
        total_videos=stats["total"],
        uploaded_videos=stats["uploaded"],
        remaining_videos=stats["remaining"],
        last_upload_at=last_upload_at,
        next_scheduled_run=scheduler_status["next_scheduled_run"],
        last_run_status=latest_run.status if latest_run else None,
        last_run_error=latest_run.error_message if latest_run else None,
    )


@router.post("/start")
def start_agent(db: Session = Depends(get_db)):
    """Enable autonomous scheduling for the agent."""
    repo = Repository(db)
    settings = repo.update_settings(enabled=True)
    SchedulerService.reschedule(settings.interval_minutes)
    return {"success": True, "message": f"Agent activated! Running every {settings.interval_minutes} minutes."}


@router.post("/stop")
def stop_agent(db: Session = Depends(get_db)):
    """Pause autonomous agent runs."""
    repo = Repository(db)
    repo.update_settings(enabled=False)
    SchedulerService.pause_job()
    return {"success": True, "message": "Agent paused."}


@router.post("/upload-now", response_model=AgentRunResult)
def trigger_upload_now(db: Session = Depends(get_db)):
    """Trigger an immediate autonomous upload run."""
    result = SchedulerService.trigger_manual_upload()
    return AgentRunResult(
        success=result.get("success", False),
        message=result.get("message", "Upload finished"),
        drive_file_id=result.get("drive_file_id"),
        file_name=result.get("file_name"),
        youtube_video_id=result.get("youtube_video_id"),
        title=result.get("title"),
        status=result.get("status"),
        error=result.get("error"),
    )
