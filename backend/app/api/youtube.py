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
    from app.services.ai_service import AIService
    ai_service = AIService(db)
    settings = repo.get_settings()

    # CRITICAL CHECK: User cannot upload a video from Drive to YouTube directly without an API key!
    if getattr(settings, "ai_provider", "gemini") == "gemini" and not ai_service.gemini_api_key:
        raise HTTPException(
            status_code=400,
            detail="Warning: Gemini API Key required! You cannot upload a video from Drive to YouTube directly without providing your Gemini API key first in Settings or Dashboard.",
        )

    video = None
    if req.video_id:
        video = repo.get_video_by_id(req.video_id)
    elif req.drive_file_id:
        video = repo.get_video_by_drive_id(req.drive_file_id)

    if not video:
        raise HTTPException(status_code=404, detail="Video record not found.")

    try:
        from pathlib import Path
        from app.utils.video_utils import extract_video_metadata

        video_service = VideoService(db)
        upload_service = UploadService(db)

        # Download if not already local
        local_path = video.local_path
        if not local_path:
            local_path = str(video_service.download_selected_video(video))

        video_file_path = Path(local_path)
        meta = extract_video_metadata(video_file_path)

        # Title: Polished by AI from raw title or filename
        raw_title = req.title or video.file_name
        title = ai_service.polish_title(raw_title=raw_title, file_name=video.file_name, video_meta=meta)

        # Description: Standard YouTube description based directly on the polished title
        description = req.description
        if not description or len(description.strip()) < 30:
            description = ai_service.generate_description(title=title, file_name=video.file_name, video_meta=meta)

        # Tags (guaranteed 15-25 SEO tags)
        tags = req.tags
        if not tags or len(tags) == 0:
            if settings.generate_tags:
                tags = ai_service.generate_tags(title, description, video.file_name)
            else:
                tags = ai_service._generate_fallback_tags(title, video.file_name)

        # 16:9 Thumbnail Generation
        thumbnail_path = None
        if getattr(settings, "generate_thumbnail", True):
            try:
                thumbnail_path = ai_service.generate_thumbnail(
                    title=title,
                    file_name=video.file_name,
                    video_path=video_file_path,
                    video_id=video.drive_file_id,
                )
            except Exception as e:
                pass

        privacy = req.privacy_status or settings.privacy_status
        category = req.category_id or settings.category_id

        record = upload_service.process_upload_with_retry(
            video=video,
            file_path=video_file_path,
            title=title,
            description=description,
            tags=tags,
            category_id=category,
            privacy_status=privacy,
            max_retries=settings.max_retries,
            thumbnail_path=thumbnail_path,
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
