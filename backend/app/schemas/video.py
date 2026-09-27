from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class DriveFolderSchema(BaseModel):
    id: Optional[int] = None
    folder_id: str
    folder_name: str
    is_selected: bool = False
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SelectFolderRequest(BaseModel):
    folder_id: str
    folder_name: Optional[str] = None


class VideoSchema(BaseModel):
    id: int
    drive_file_id: str
    file_name: str
    mime_type: str
    size: int
    drive_folder_id: Optional[str] = None
    status: str
    local_path: Optional[str] = None
    duration: Optional[int] = None
    resolution: Optional[str] = None
    fps: Optional[str] = None
    codec: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    youtube_video_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VideoListResponse(BaseModel):
    total: int
    uploaded_count: int
    remaining_count: int
    videos: List[VideoSchema]


class VideoStatsResponse(BaseModel):
    total_videos: int
    uploaded_videos: int
    remaining_videos: int
    failed_videos: int
    current_folder: Optional[str] = None
    current_folder_name: Optional[str] = None
