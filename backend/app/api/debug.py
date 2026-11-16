from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.debug_service import DebugService, update_agent_pipeline_state


router = APIRouter(prefix="/api/debug", tags=["Agent Debugger & Diagnostics"])


class SimulateRequest(BaseModel):
    video_title: Optional[str] = None


@router.get("/pipeline-state")
def get_live_pipeline_state(db: Session = Depends(get_db)):
    """Get current in-memory AI Agent pipeline state, active subtask, and step logs."""
    service = DebugService(db)
    return service.get_live_pipeline_state()


@router.get("/diagnostics")
def get_system_diagnostics(db: Session = Depends(get_db)):
    """Run full system health checks across Auth, Drive, YouTube, Gemini AI, DB, and Scheduler."""
    service = DebugService(db)
    return service.get_system_diagnostics()


@router.post("/simulate-ai")
def simulate_ai_reasoning(
    payload: SimulateRequest = Body(default=SimulateRequest()),
    db: Session = Depends(get_db),
):
    """
    Test/debug AI generation logic (Gemini 2.5 Flash-Lite & Imagen 3 prompt engineering)
    for a given video title or random remaining video.
    """
    try:
        service = DebugService(db)
        return service.simulate_ai_pipeline(payload.video_title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-pipeline-state")
def reset_pipeline_state():
    """Reset the live pipeline state tracker to idle."""
    update_agent_pipeline_state(
        status="idle",
        step_id="idle",
        step_label="System Ready & Idle",
        progress=0,
        current_video=None,
        log_message="Pipeline state reset manually via Debugger.",
    )
    return {"success": True, "message": "Pipeline state reset."}
