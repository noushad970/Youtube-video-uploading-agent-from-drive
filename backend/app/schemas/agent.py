from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class AgentStatusResponse(BaseModel):
    is_running: bool
    is_scheduler_running: bool
    is_job_active: bool
    google_connected: bool
    youtube_connected: bool
    drive_connected: bool
    ollama_connected: bool
    selected_folder_name: Optional[str] = None
    selected_folder_id: Optional[str] = None
    total_videos: int = 0
    uploaded_videos: int = 0
    remaining_videos: int = 0
    last_upload_at: Optional[datetime] = None
    next_scheduled_run: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_error: Optional[str] = None


class AgentRunResult(BaseModel):
    success: bool
    message: str
    drive_file_id: Optional[str] = None
    file_name: Optional[str] = None
    youtube_video_id: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None


class LogEntrySchema(BaseModel):
    id: int
    level: str
    message: str
    details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LogListResponse(BaseModel):
    total: int
    logs: List[LogEntrySchema]
