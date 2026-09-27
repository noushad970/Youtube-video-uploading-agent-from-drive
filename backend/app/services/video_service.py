from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import logger
from app.database.repository import Repository
from app.database.models import Video
from app.services.drive_service import DriveService
from app.utils.file_utils import sanitize_filename, safe_delete_file
from app.utils.video_utils import extract_video_metadata, extract_video_thumbnail


class VideoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = Repository(db)
        self.drive_service = DriveService(db)

    def download_selected_video(self, video: Video) -> Path:
        """
        Download a specific video to the data/videos directory.
        Uses format: {drive_file_id}_{sanitized_file_name}
        Updates video record with local_path and extracted metadata.
        """
        clean_name = sanitize_filename(video.file_name)
        file_dest = Path(settings.DOWNLOAD_DIRECTORY) / f"{video.drive_file_id}_{clean_name}"

        # Update state to downloading
        self.repo.update_video(video.id, status="downloading")

        try:
            downloaded_path = self.drive_service.download_video(video.drive_file_id, file_dest)
            
            # Extract video technical metadata (duration, resolution, fps, codec)
            meta = extract_video_metadata(downloaded_path)
            self.repo.update_video(
                video.id,
                local_path=str(downloaded_path),
                status="processing",
                duration=meta.get("duration"),
                resolution=meta.get("resolution"),
                fps=meta.get("fps"),
                codec=meta.get("video_codec"),
            )
            return downloaded_path
        except Exception as e:
            logger.error(f"Failed to download video {video.file_name}: {e}")
            self.repo.update_video(video.id, status="failed")
            safe_delete_file(file_dest)
            raise

    def cleanup_video(self, video: Video, force: bool = False) -> None:
        """Clean up local temporary video file based on user settings or force flag."""
        app_settings = self.repo.get_settings()
        if force or app_settings.delete_after_upload:
            if video.local_path:
                safe_delete_file(video.local_path)
                self.repo.update_video(video.id, local_path=None)
