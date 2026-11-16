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
from app.services.debug_service import update_agent_pipeline_state
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
        6. Generate AI thumbnail (Imagen 3)
        7. Upload to YouTube as private/configured status
        8. Set custom thumbnail & record upload
        9. Clean up temporary files
        """
        logger.info("--- YouTube AI Agent execution triggered ---")
        update_agent_pipeline_state(
            status="running",
            step_id="authenticating",
            step_label="Checking Google OAuth & Permissions",
            progress=10,
            log_message="Agent initialized. Verifying Google OAuth token...",
        )
        settings: AgentSettings = self.repo.get_settings()

        if not force_run and not settings.enabled:
            logger.info("Agent is currently disabled in settings. Skipping run.")
            update_agent_pipeline_state(
                status="idle",
                step_id="idle",
                step_label="Agent Disabled",
                progress=0,
                log_message="Agent disabled in settings. Skipping automatic run.",
            )
            return {"success": False, "message": "Agent is disabled. Enable agent or use manual upload."}

        # 1. Check Google Auth
        auth_status = self.auth_service.get_auth_status()
        if not auth_status["is_authenticated"]:
            logger.error("Google account is not authenticated.")
            update_agent_pipeline_state(
                status="error",
                step_id="auth_failed",
                step_label="Google Authentication Failed",
                progress=0,
                log_message="Error: Google Account not authenticated. Connect account in settings.",
            )
            return {"success": False, "message": "Google account not authenticated."}

        # 2. Check Drive folder configuration
        selected_folder = self.repo.get_selected_folder()
        if not selected_folder:
            logger.error("No Google Drive folder selected for monitoring.")
            update_agent_pipeline_state(
                status="error",
                step_id="folder_missing",
                step_label="No Drive Folder Selected",
                progress=0,
                log_message="Error: No Google Drive folder selected for sync.",
            )
            return {"success": False, "message": "No Google Drive folder selected."}

        # 3. Synchronize folder to discover any newly added files
        update_agent_pipeline_state(
            status="running",
            step_id="scanning_drive",
            step_label=f"Scanning Drive folder '{selected_folder.folder_name}'",
            progress=25,
            log_message=f"Syncing files from Drive folder '{selected_folder.folder_name}'...",
        )
        try:
            self.drive_service.sync_folder_videos(
                selected_folder.folder_id,
                selected_folder.folder_name,
            )
        except Exception as e:
            logger.warning(f"Unable to sync latest Drive folder contents: {e}")

        # 4. Select random unuploaded video
        update_agent_pipeline_state(
            status="running",
            step_id="selecting_video",
            step_label="Selecting Target Video",
            progress=35,
            log_message="Querying database for next unuploaded video...",
        )
        video: Optional[Video] = self.repo.select_random_unuploaded_video(selected_folder.folder_id)
        if not video:
            logger.info("No unuploaded videos found in the selected folder. All videos uploaded!")
            update_agent_pipeline_state(
                status="idle",
                step_id="all_uploaded",
                step_label="All Videos Uploaded",
                progress=100,
                log_message="All videos in Drive folder have been uploaded.",
            )
            return {
                "success": False,
                "message": "No unuploaded videos remaining in folder.",
                "total_videos": self.repo.get_video_stats(selected_folder.folder_id)["total"],
            }

        logger.info(f"Selected video for upload: '{video.file_name}' (ID: {video.drive_file_id})")
        update_agent_pipeline_state(
            status="running",
            step_id="downloading",
            step_label=f"Downloading '{video.file_name}'",
            progress=45,
            current_video=video.file_name,
            log_message=f"Starting download from Drive: {video.file_name}...",
        )

        # 5. Create AgentRun tracking entry
        agent_run = self.repo.create_agent_run(video_id=video.id)

        local_file_path = None
        try:
            # 6. Download Video
            logger.info(f"Downloading video '{video.file_name}' from Drive...")
            local_file_path = self.video_service.download_selected_video(video)

            # 7. Extract metadata
            update_agent_pipeline_state(
                status="running",
                step_id="analyzing_video",
                step_label="Analyzing Video Metadata",
                progress=60,
                current_video=video.file_name,
                log_message="Extracting video stream codec, resolution and duration...",
            )
            meta = extract_video_metadata(local_file_path)

            # 8. Generate Metadata (Title, Description, Tags)
            provider_name = getattr(settings, "ai_provider", "gemini")
            model_name = getattr(settings, "gemini_model", "gemini-2.5-flash-lite") if provider_name == "gemini" else getattr(settings, "ollama_model", "qwen3:8b")
            update_agent_pipeline_state(
                status="running",
                step_id="generating_metadata",
                step_label=f"AI Reasoning ({provider_name.upper()} - {model_name})",
                progress=72,
                current_video=video.file_name,
                log_message=f"Prompting {provider_name.upper()} AI for viral YouTube title, description and tags...",
            )
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

            # 9. Generate AI Thumbnail via Gemini Imagen (if enabled)
            thumbnail_path = None
            if getattr(settings, "generate_thumbnail", True):
                try:
                    update_agent_pipeline_state(
                        status="running",
                        step_id="generating_thumbnail",
                        step_label="Generating 16:9 Thumbnail",
                        progress=82,
                        current_video=video.file_name,
                        log_message=f"Generating high-impact 16:9 thumbnail for '{title}'...",
                    )
                    logger.info("Generating thumbnail for video...")
                    thumbnail_path = self.ai_service.generate_thumbnail(
                        title=title,
                        file_name=video.file_name,
                        video_path=local_file_path,
                        video_id=video.drive_file_id,
                    )
                    if thumbnail_path:
                        logger.info(f"Video thumbnail generated successfully: {thumbnail_path}")
                    else:
                        logger.warning("Thumbnail generation returned None")
                except Exception as e:
                    logger.warning(f"AI thumbnail generation failed/skipped: {e}")

            # 10. Upload to YouTube
            update_agent_pipeline_state(
                status="running",
                step_id="uploading_youtube",
                step_label="Streaming Upload to YouTube Data API",
                progress=90,
                current_video=video.file_name,
                log_message="Streaming video bytes & setting metadata via YouTube Data API v3...",
            )
            upload_record = self.upload_service.process_upload_with_retry(
                video=video,
                file_path=local_file_path,
                title=title,
                description=description,
                tags=tags,
                category_id=settings.category_id,
                privacy_status=settings.privacy_status,
                max_retries=settings.max_retries,
                thumbnail_path=thumbnail_path,
            )

            # 11. Clean up temporary local file
            self.video_service.cleanup_video(video)

            # 12. Complete Agent Run
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
            update_agent_pipeline_state(
                status="success",
                step_id="complete",
                step_label=f"Upload Complete (ID: {upload_record.youtube_video_id})",
                progress=100,
                current_video=video.file_name,
                log_message=f"Pipeline succeeded! YouTube video published: https://youtu.be/{upload_record.youtube_video_id}",
                last_result=result,
            )
            return result

        except Exception as e:
            err_trace = traceback.format_exc()
            logger.error(f"Agent run failed: {e}\n{err_trace}")
            self.repo.finish_agent_run(agent_run.id, status="failed", error_message=str(e))
            self.video_service.cleanup_video(video)
            err_result = {
                "success": False,
                "message": f"Agent run failed: {str(e)}",
                "error": str(e),
                "drive_file_id": video.drive_file_id,
                "file_name": video.file_name,
            }
            update_agent_pipeline_state(
                status="error",
                step_id="failed",
                step_label="Pipeline Execution Error",
                progress=0,
                current_video=video.file_name,
                log_message=f"Error occurred during upload execution: {str(e)}",
                last_result=err_result,
            )
            return err_result

