from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.repository import Repository
from app.schemas.youtube import UploadListResponse, UploadRecordSchema

router = APIRouter(prefix="/api/uploads", tags=["Uploads History"])


@router.get("", response_model=UploadListResponse)
def list_uploads(
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve history of YouTube upload attempts and successes."""
    repo = Repository(db)
    total, items = repo.list_uploads(
        status=status,
        search=search,
        skip=skip,
        limit=limit,
    )

    records = []
    for u in items:
        import json
        tags_list = json.loads(u.tags) if u.tags else []
        records.append(
            UploadRecordSchema(
                id=u.id,
                video_id=u.video_id,
                youtube_video_id=u.youtube_video_id,
                title=u.title,
                description=u.description,
                tags=tags_list,
                category_id=u.category_id,
                privacy_status=u.privacy_status,
                status=u.status,
                retry_count=u.retry_count,
                error_message=u.error_message,
                uploaded_at=u.uploaded_at,
                created_at=u.created_at,
                updated_at=u.updated_at,
                thumbnail_path=u.thumbnail_path,
                file_name=u.video.file_name if u.video else None,
                drive_file_id=u.video.drive_file_id if u.video else None,
            )
        )

    return UploadListResponse(total=total, items=records)


@router.get("/{upload_id}", response_model=UploadRecordSchema)
def get_upload_detail(upload_id: int, db: Session = Depends(get_db)):
    """Get single upload record details."""
    repo = Repository(db)
    u = repo.get_upload_by_id(upload_id)
    if not u:
        raise HTTPException(status_code=404, detail="Upload record not found")

    import json
    tags_list = json.loads(u.tags) if u.tags else []
    return UploadRecordSchema(
        id=u.id,
        video_id=u.video_id,
        youtube_video_id=u.youtube_video_id,
        title=u.title,
        description=u.description,
        tags=tags_list,
        category_id=u.category_id,
        privacy_status=u.privacy_status,
        status=u.status,
        retry_count=u.retry_count,
        error_message=u.error_message,
        uploaded_at=u.uploaded_at,
        created_at=u.created_at,
        updated_at=u.updated_at,
        file_name=u.video.file_name if u.video else None,
        drive_file_id=u.video.drive_file_id if u.video else None,
    )
