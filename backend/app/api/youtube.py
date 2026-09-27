from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.youtube_service import YouTubeService
from app.services.upload_service import UploadService
from app.services.video_service import VideoService
from app.schemas.youtube import YouTubeChannelInfo, YouTubeUploadRequest, YouTubeUploadResponse
from app.database.repository import Repository

router = APIRouter(prefix="/api/youtube", tags=["YouTube"])


@router.get("/channel", response_model=YouTubeChannelInfo)
def get_channel_info(db: Session = Depends(get_db)):
    """Fetch authorized YouTube Channel details."""
    try:
        service = YouTubeService(db)
        info = service.get_channel_info()
        return YouTubeChannelInfo(**info)
    except PermissionError as pe:
        raise HTTPException(status_code=401, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch YouTube channel: {e}")


@router.post("/upload", response_model=YouTubeUploadResponse)
def manual_upload_video(
    req: YouTubeUploadRequest,
    db: Session = Depends(get_db),
):
    """Manually trigger upload of a specific video by ID or Drive File ID."""
    repo = Repository(db)
    video = None
    if req.video_id:
        video = repo.get_video_by_id(req.video_id)
    elif req.drive_file_id:
        video = repo.get_video_by_drive_id(req.drive_file_id)

    if not video:
        raise HTTPException(status_code=404, detail="Video record not found.")

    try:
        video_service = VideoService(db)
        upload_service = UploadService(db)
        settings = repo.get_settings()

        # Download if not already local
        local_path = video.local_path
        if not local_path:
            local_path = str(video_service.download_selected_video(video))

        from pathlib import Path
        title = req.title or video.file_name
        description = req.description or f"{title}\n\nUploaded via YouTube AI Agent."
        tags = req.tags or []
        privacy = req.privacy_status or settings.privacy_status
        category = req.category_id or settings.category_id

        record = upload_service.process_upload_with_retry(
            video=video,
            file_path=Path(local_path),
            title=title,
            description=description,
            tags=tags,
            category_id=category,
            privacy_status=privacy,
            max_retries=settings.max_retries,
        )

        video_service.cleanup_video(video)

        return YouTubeUploadResponse(
            success=True,
            youtube_video_id=record.youtube_video_id,
            title=record.title,
            privacy_status=record.privacy_status,
            uploaded_at=record.uploaded_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
