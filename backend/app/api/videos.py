from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.repository import Repository
from app.services.drive_service import DriveService
from app.schemas.video import VideoSchema, VideoListResponse, VideoStatsResponse

router = APIRouter(prefix="/api/videos", tags=["Videos"])


@router.get("", response_model=VideoListResponse)
def list_videos(
    folder_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List videos cataloged in database with filter and pagination."""
    repo = Repository(db)
    total, videos = repo.list_videos(
        folder_id=folder_id,
        status=status,
        search=search,
        skip=skip,
        limit=limit,
    )
    stats = repo.get_video_stats(folder_id)

    video_schemas = []
    for v in videos:
        # Get youtube_video_id if uploaded
        yt_id = None
        if v.uploads:
            latest_upload = v.uploads[-1]
            yt_id = latest_upload.youtube_video_id
        
        schema = VideoSchema(
            id=v.id,
            drive_file_id=v.drive_file_id,
            file_name=v.file_name,
            mime_type=v.mime_type,
            size=v.size,
            drive_folder_id=v.drive_folder_id,
            status=v.status,
            local_path=v.local_path,
            duration=v.duration,
            resolution=v.resolution,
            fps=v.fps,
            codec=v.codec,
            created_at=v.created_at,
            updated_at=v.updated_at,
            youtube_video_id=yt_id,
        )
        video_schemas.append(schema)

    return VideoListResponse(
        total=total,
        uploaded_count=stats["uploaded"],
        remaining_count=stats["remaining"],
        videos=video_schemas,
    )


@router.get("/stats", response_model=VideoStatsResponse)
def get_video_stats(
    folder_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Retrieve overview counts for videos."""
    repo = Repository(db)
    selected = repo.get_selected_folder()
    target_folder_id = folder_id or (selected.folder_id if selected else None)
    target_folder_name = selected.folder_name if selected else None

    stats = repo.get_video_stats(target_folder_id)
    return VideoStatsResponse(
        total_videos=stats["total"],
        uploaded_videos=stats["uploaded"],
        remaining_videos=stats["remaining"],
        failed_videos=stats["failed"],
        current_folder=target_folder_id,
        current_folder_name=target_folder_name,
    )


@router.post("/{video_id}/reset", response_model=VideoSchema)
def reset_video_status(video_id: int, db: Session = Depends(get_db)):
    """Reset video upload status to available to allow re-uploading."""
    repo = Repository(db)
    video = repo.reset_video_upload_status(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return VideoSchema(
        id=video.id,
        drive_file_id=video.drive_file_id,
        file_name=video.file_name,
        mime_type=video.mime_type,
        size=video.size,
        drive_folder_id=video.drive_folder_id,
        status=video.status,
        local_path=video.local_path,
        duration=video.duration,
        resolution=video.resolution,
        fps=video.fps,
        codec=video.codec,
        created_at=video.created_at,
        updated_at=video.updated_at,
        youtube_video_id=None,
    )


@router.post("/sync")
def sync_drive_videos(db: Session = Depends(get_db)):
    """Trigger manual scan and synchronization of selected Drive folder."""
    repo = Repository(db)
    selected = repo.get_selected_folder()
    if not selected:
        raise HTTPException(status_code=400, detail="No Drive folder selected.")

    drive_service = DriveService(db)
    videos = drive_service.sync_folder_videos(selected.folder_id, selected.folder_name)
    return {"success": True, "count": len(videos), "folder_name": selected.folder_name}
