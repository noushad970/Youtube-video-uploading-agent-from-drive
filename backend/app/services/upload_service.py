import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.database.repository import Repository
from app.database.models import Video, Upload
from app.services.youtube_service import YouTubeService


class UploadService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = Repository(db)
        self.youtube_service = YouTubeService(db)

    def process_upload_with_retry(
        self,
        video: Video,
        file_path: Path,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        category_id: str = "20",
        privacy_status: str = "private",
        max_retries: int = 3,
    ) -> Upload:
        """
        Execute YouTube upload with safe duplicate prevention, exponential backoff retries,
        and atomic status tracking.
        """
        # 1. Check if already uploaded
        existing_upload = (
            self.db.query(Upload)
            .filter(Upload.video_id == video.id, Upload.status == "uploaded")
            .first()
        )
        if existing_upload and existing_upload.youtube_video_id:
            logger.warning(
                f"Video '{video.file_name}' was already successfully uploaded as {existing_upload.youtube_video_id}. "
                "Skipping duplicate upload."
            )
            self.repo.update_video(video.id, status="uploaded")
            return existing_upload

        # 2. Create pending Upload record
        upload_record = self.repo.create_upload(
            video_id=video.id,
            title=title,
            description=description,
            tags=tags,
            category_id=category_id,
            privacy_status=privacy_status,
        )

        # 3. Mark video as uploading
        self.repo.update_video(video.id, status="uploading")
        self.repo.update_upload(upload_record.id, status="uploading")

        # 4. Attempt upload with exponential backoff
        attempt = 0
        backoff_sec = 10.0
        last_error: Optional[Exception] = None

        while attempt < max_retries:
            attempt += 1
            try:
                logger.info(
                    f"Upload attempt {attempt}/{max_retries} for video '{video.file_name}'..."
                )
                yt_video_id = self.youtube_service.upload_video(
                    file_path=file_path,
                    title=title,
                    description=description,
                    tags=tags,
                    category_id=category_id,
                    privacy_status=privacy_status,
                )

                # Successful upload state transition
                self.repo.update_upload(
                    upload_record.id,
                    status="uploaded",
                    youtube_video_id=yt_video_id,
                    retry_count=attempt - 1,
                    uploaded_at=datetime.now(timezone.utc),
                    error_message=None,
                )
                self.repo.update_video(video.id, status="uploaded")
                logger.info(
                    f"Successfully uploaded '{video.file_name}' to YouTube (ID: {yt_video_id})"
                )
                return upload_record

            except Exception as e:
                last_error = e
                logger.error(
                    f"Upload attempt {attempt}/{max_retries} failed for '{video.file_name}': {e}"
                )
                self.repo.update_upload(
                    upload_record.id,
                    retry_count=attempt,
                    error_message=str(e),
                )
                if attempt < max_retries:
                    logger.info(f"Retrying upload in {backoff_sec} seconds...")
                    time.sleep(backoff_sec)
                    backoff_sec *= 2.0

        # All retry attempts failed
        error_msg = f"Failed after {max_retries} attempts: {last_error}"
        self.repo.update_upload(
            upload_record.id,
            status="failed",
            error_message=error_msg,
        )
        self.repo.update_video(video.id, status="failed")
        raise RuntimeError(error_msg)
