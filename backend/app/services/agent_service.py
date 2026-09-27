import traceback
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.database.repository import Repository
from app.database.models import Video, AgentSettings
from app.services.google_auth_service import GoogleAuthService
from app.services.drive_service import DriveService
from app.services.video_service import VideoService
from app.services.ai_service import AIService
from app.services.youtube_service import YouTubeService
from app.services.upload_service import UploadService
from app.utils.video_utils import extract_video_metadata


class AgentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = Repository(db)
        self.auth_service = GoogleAuthService(db)
        self.drive_service = DriveService(db)
        self.video_service = VideoService(db)
        self.ai_service = AIService(db)
        self.youtube_service = YouTubeService(db)
        self.upload_service = UploadService(db)

    def run_upload_agent(self, force_run: bool = False) -> Dict[str, Any]:
        """
        Execute one complete autonomous run of the YouTube Upload Agent:
        1. Verify Google authentication & scopes
        2. Verify selected Drive folder
        3. Synchronize catalog & select random unuploaded video
        4. Download video
        5. Extract metadata & generate AI title, description, tags
        6. Upload to YouTube as private/configured status
        7. Record upload & mark as uploaded
        8. Clean up temporary files
        """
        logger.info("--- YouTube AI Agent execution triggered ---")
        settings: AgentSettings = self.repo.get_settings()

        if not force_run and not settings.enabled:
            logger.info("Agent is currently disabled in settings. Skipping run.")
            return {"success": False, "message": "Agent is disabled. Enable agent or use manual upload."}

        # 1. Check Google Auth
        auth_status = self.auth_service.get_auth_status()
        if not auth_status["is_authenticated"]:
            logger.error("Google account is not authenticated.")
            return {"success": False, "message": "Google account not authenticated."}

        # 2. Check Drive folder configuration
        selected_folder = self.repo.get_selected_folder()
        if not selected_folder:
            logger.error("No Google Drive folder selected for monitoring.")
            return {"success": False, "message": "No Google Drive folder selected."}

        # 3. Synchronize folder to discover any newly added files
        try:
            self.drive_service.sync_folder_videos(
                selected_folder.folder_id,
                selected_folder.folder_name,
            )
        except Exception as e:
            logger.warning(f"Unable to sync latest Drive folder contents: {e}")

        # 4. Select random unuploaded video
        video: Optional[Video] = self.repo.select_random_unuploaded_video(selected_folder.folder_id)
        if not video:
            logger.info("No unuploaded videos found in the selected folder. All videos uploaded!")
            return {
                "success": False,
                "message": "No unuploaded videos remaining in folder.",
                "total_videos": self.repo.get_video_stats(selected_folder.folder_id)["total"],
            }

        logger.info(f"Selected video for upload: '{video.file_name}' (ID: {video.drive_file_id})")

        # 5. Create AgentRun tracking entry
        agent_run = self.repo.create_agent_run(video_id=video.id)

        local_file_path = None
        try:
            # 6. Download Video
            logger.info(f"Downloading video '{video.file_name}' from Drive...")
            local_file_path = self.video_service.download_selected_video(video)

            # 7. Extract metadata
            meta = extract_video_metadata(local_file_path)

            # 8. Generate Metadata (Title, Description, Tags)
            logger.info("Generating metadata via AI Service...")
            if settings.generate_title:
                title = self.ai_service.generate_title(video.file_name, meta)
            else:
                title = self.ai_service._clean_filename_to_title(video.file_name)

            if settings.generate_description:
                description = self.ai_service.generate_description(title, video.file_name, meta)
            else:
                description = f"{title}\n\nUploaded via YouTube AI Agent."

            tags = []
            if settings.generate_tags:
                tags = self.ai_service.generate_tags(title, description, video.file_name)

            logger.info(f"Generated YouTube Title: '{title}'")
            logger.info(f"Generated Tags ({len(tags)}): {tags}")

            # 9. Upload to YouTube
            upload_record = self.upload_service.process_upload_with_retry(
                video=video,
                file_path=local_file_path,
                title=title,
                description=description,
                tags=tags,
                category_id=settings.category_id,
                privacy_status=settings.privacy_status,
                max_retries=settings.max_retries,
            )

            # 10. Clean up temporary local file
            self.video_service.cleanup_video(video)

            # 11. Complete Agent Run
            self.repo.finish_agent_run(
                agent_run.id,
                status="success",
                details=f"Uploaded video '{video.file_name}' -> YouTube ID: {upload_record.youtube_video_id}",
            )

            result = {
                "success": True,
                "message": f"Successfully uploaded {video.file_name}",
                "drive_file_id": video.drive_file_id,
                "file_name": video.file_name,
                "youtube_video_id": upload_record.youtube_video_id,
                "title": title,
                "status": settings.privacy_status,
            }
            logger.info(f"Agent run completed successfully: {result}")
            return result

        except Exception as e:
            err_trace = traceback.format_exc()
            logger.error(f"Agent run failed: {e}\n{err_trace}")
            self.repo.finish_agent_run(agent_run.id, status="failed", error_message=str(e))
            self.video_service.cleanup_video(video)
            return {
                "success": False,
                "message": f"Agent run failed: {str(e)}",
                "error": str(e),
                "drive_file_id": video.drive_file_id,
                "file_name": video.file_name,
            }
