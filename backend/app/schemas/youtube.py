from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class YouTubeChannelInfo(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    custom_url: Optional[str] = None
    published_at: Optional[str] = None
    thumbnail_url: Optional[str] = None
    subscriber_count: Optional[str] = None
    video_count: Optional[str] = None
    view_count: Optional[str] = None


class YouTubeUploadRequest(BaseModel):
    video_id: Optional[int] = None
    drive_file_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category_id: Optional[str] = "20"
    privacy_status: Optional[str] = "private"


class YouTubeUploadResponse(BaseModel):
    success: bool
    youtube_video_id: Optional[str] = None
    title: str
    privacy_status: str
    uploaded_at: Optional[datetime] = None
    error_message: Optional[str] = None


class UploadRecordSchema(BaseModel):
    id: int
    video_id: int
    youtube_video_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category_id: str
    privacy_status: str
    status: str
    retry_count: int
    error_message: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    file_name: Optional[str] = None
    drive_file_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UploadListResponse(BaseModel):
    total: int
    items: List[UploadRecordSchema]
