import json
import random
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from app.database.models import (
    User,
    GoogleCredential,
    DriveFolder,
    Video,
    Upload,
    AgentSettings,
    AgentRun,
    LogEntry,
)
from app.core.security import encrypt_token, decrypt_token


class Repository:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------
    # Settings
    # -------------------------------------------------------------
    def get_settings(self) -> AgentSettings:
        settings = self.db.query(AgentSettings).first()
        if not settings:
            settings = AgentSettings(
                enabled=False,
                interval_minutes=360,
                privacy_status="private",
                category_id="20",
                generate_title=True,
                generate_description=True,
                generate_tags=True,
                ollama_model="qwen3:8b",
                max_retries=3,
                delete_after_upload=True,
                fallback_if_ai_unavailable=True,
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        return settings

    def update_settings(self, **kwargs) -> AgentSettings:
        settings = self.get_settings()
        for k, v in kwargs.items():
            if v is not None and hasattr(settings, k):
                setattr(settings, k, v)
        settings.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    # -------------------------------------------------------------
    # User & Google Credentials
    # -------------------------------------------------------------
    def get_user(self, email: Optional[str] = None) -> Optional[User]:
        if email:
            return self.db.query(User).filter(User.email == email).first()
        return self.db.query(User).first()

    def upsert_user(self, email: str, name: Optional[str] = None, picture: Optional[str] = None) -> User:
        user = self.get_user(email)
        if not user:
            user = User(email=email, name=name, picture=picture)
            self.db.add(user)
        else:
            if name:
                user.name = name
            if picture:
                user.picture = picture
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_credential(self, user_id: Optional[int] = None) -> Optional[GoogleCredential]:
        query = self.db.query(GoogleCredential)
        if user_id:
            cred = query.filter(GoogleCredential.user_id == user_id).first()
        else:
            cred = query.order_by(desc(GoogleCredential.updated_at)).first()
        
        if cred and cred.access_token:
            # We clone decrypted attributes for in-memory use without mutating db session
            cred.decrypted_access_token = decrypt_token(cred.access_token)
            cred.decrypted_refresh_token = decrypt_token(cred.refresh_token)
        return cred

    def save_credential(
        self,
        user_id: int,
        access_token: str,
        refresh_token: Optional[str],
        token_expiry: Optional[datetime],
        scopes: str,
    ) -> GoogleCredential:
        encrypted_access = encrypt_token(access_token)
        encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None

        cred = self.db.query(GoogleCredential).filter(GoogleCredential.user_id == user_id).first()
        if not cred:
            cred = GoogleCredential(
                user_id=user_id,
                access_token=encrypted_access,
                refresh_token=encrypted_refresh,
                token_expiry=token_expiry,
                scopes=scopes,
            )
            self.db.add(cred)
        else:
            cred.access_token = encrypted_access
            if encrypted_refresh:
                cred.refresh_token = encrypted_refresh
            cred.token_expiry = token_expiry
            cred.scopes = scopes
            cred.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(cred)
        return cred

    def delete_all_credentials(self) -> None:
        self.db.query(GoogleCredential).delete()
        self.db.query(User).delete()
        self.db.commit()

    # -------------------------------------------------------------
    # Drive Folders
    # -------------------------------------------------------------
    def get_all_folders(self) -> List[DriveFolder]:
        return self.db.query(DriveFolder).order_by(DriveFolder.folder_name).all()

    def get_selected_folder(self) -> Optional[DriveFolder]:
        return self.db.query(DriveFolder).filter(DriveFolder.is_selected == True).first()

    def select_folder(self, folder_id: str, folder_name: str, user_id: Optional[int] = None) -> DriveFolder:
        # Deselect any currently selected folder
        self.db.query(DriveFolder).update({DriveFolder.is_selected: False})
        
        folder = self.db.query(DriveFolder).filter(DriveFolder.folder_id == folder_id).first()
        if not folder:
            folder = DriveFolder(
                folder_id=folder_id,
                folder_name=folder_name,
                is_selected=True,
                user_id=user_id,
            )
            self.db.add(folder)
        else:
            folder.folder_name = folder_name
            folder.is_selected = True
            if user_id:
                folder.user_id = user_id
            folder.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(folder)
        return folder

    # -------------------------------------------------------------
    # Videos
    # -------------------------------------------------------------
    def upsert_video_from_drive(
        self,
        drive_file_id: str,
        file_name: str,
        mime_type: str,
        size: int,
        folder_id: Optional[str] = None,
    ) -> Video:
        video = self.db.query(Video).filter(Video.drive_file_id == drive_file_id).first()
        if not video:
            video = Video(
                drive_file_id=drive_file_id,
                file_name=file_name,
                mime_type=mime_type,
                size=size,
                drive_folder_id=folder_id,
                status="available",
            )
            self.db.add(video)
        else:
            video.file_name = file_name
            video.mime_type = mime_type
            video.size = size
            if folder_id:
                video.drive_folder_id = folder_id
            video.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(video)
        return video

    def get_video_by_drive_id(self, drive_file_id: str) -> Optional[Video]:
        return self.db.query(Video).filter(Video.drive_file_id == drive_file_id).first()

    def get_video_by_id(self, video_id: int) -> Optional[Video]:
        return self.db.query(Video).filter(Video.id == video_id).first()

    def update_video(self, video_id: int, **kwargs) -> Optional[Video]:
        video = self.get_video_by_id(video_id)
        if not video:
            return None
        for k, v in kwargs.items():
            if hasattr(video, k):
                setattr(video, k, v)
        video.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(video)
        return video

    def list_videos(
        self,
        folder_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[int, List[Video]]:
        query = self.db.query(Video)
        if folder_id:
            query = query.filter(Video.drive_folder_id == folder_id)
        if status:
            query = query.filter(Video.status == status)
        if search:
            query = query.filter(Video.file_name.ilike(f"%{search}%"))

        total = query.count()
        videos = query.order_by(desc(Video.created_at)).offset(skip).limit(limit).all()
        return total, videos

    def select_random_unuploaded_video(self, folder_id: Optional[str] = None) -> Optional[Video]:
        """
        Algorithm:
        1. Query videos for folder_id.
        2. Filter out videos whose status is 'uploaded', 'uploading', or 'downloading'.
        3. Exclude videos that have successful Upload records.
        4. Pick one randomly.
        """
        uploaded_video_ids = (
            self.db.query(Upload.video_id)
            .filter(Upload.status == "uploaded")
            .scalar_subquery()
        )

        query = self.db.query(Video).filter(
            Video.status.notin_(["uploaded", "uploading", "downloading"]),
            ~Video.id.in_(uploaded_video_ids),
        )

        if folder_id:
            query = query.filter(Video.drive_folder_id == folder_id)

        available_videos = query.all()
        if not available_videos:
            return None

        return random.choice(available_videos)

    def get_video_stats(self, folder_id: Optional[str] = None) -> dict:
        query = self.db.query(Video)
        if folder_id:
            query = query.filter(Video.drive_folder_id == folder_id)

        total = query.count()
        uploaded = query.filter(Video.status == "uploaded").count()
        failed = query.filter(Video.status == "failed").count()
        remaining = max(0, total - uploaded)

        return {
            "total": total,
            "uploaded": uploaded,
            "remaining": remaining,
            "failed": failed,
        }

    # -------------------------------------------------------------
    # Uploads
    # -------------------------------------------------------------
    def create_upload(
        self,
        video_id: int,
        title: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category_id: str = "20",
        privacy_status: str = "private",
    ) -> Upload:
        tags_json = json.dumps(tags) if tags else None
        upload = Upload(
            video_id=video_id,
            title=title,
            description=description,
            tags=tags_json,
            category_id=category_id,
            privacy_status=privacy_status,
            status="pending",
        )
        self.db.add(upload)
        self.db.commit()
        self.db.refresh(upload)
        return upload

    def update_upload(self, upload_id: int, **kwargs) -> Optional[Upload]:
        upload = self.db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            return None
        for k, v in kwargs.items():
            if k == "tags" and isinstance(v, list):
                upload.tags = json.dumps(v)
            elif hasattr(upload, k):
                setattr(upload, k, v)
        upload.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(upload)
        return upload

    def list_uploads(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[int, List[Upload]]:
        query = self.db.query(Upload).join(Video)
        if status:
            query = query.filter(Upload.status == status)
        if search:
            query = query.filter(
                or_(
                    Upload.title.ilike(f"%{search}%"),
                    Upload.youtube_video_id.ilike(f"%{search}%"),
                    Video.file_name.ilike(f"%{search}%"),
                )
            )

        total = query.count()
        uploads = query.order_by(desc(Upload.created_at)).offset(skip).limit(limit).all()
        return total, uploads

    def get_upload_by_id(self, upload_id: int) -> Optional[Upload]:
        return self.db.query(Upload).filter(Upload.id == upload_id).first()

    def reset_video_upload_status(self, video_id: int) -> Optional[Video]:
        video = self.get_video_by_id(video_id)
        if not video:
            return None
        video.status = "available"
        video.updated_at = datetime.now(timezone.utc)
        # Also remove existing failed/uploaded records to allow fresh upload
        self.db.query(Upload).filter(Upload.video_id == video_id).delete()
        self.db.commit()
        self.db.refresh(video)
        return video

    # -------------------------------------------------------------
    # Agent Runs
    # -------------------------------------------------------------
    def create_agent_run(self, video_id: Optional[int] = None) -> AgentRun:
        run = AgentRun(
            started_at=datetime.now(timezone.utc),
            status="running",
            video_id=video_id,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def finish_agent_run(
        self,
        run_id: int,
        status: str,
        error_message: Optional[str] = None,
        details: Optional[str] = None,
    ) -> Optional[AgentRun]:
        run = self.db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if not run:
            return None
        run.finished_at = datetime.now(timezone.utc)
        run.status = status
        run.error_message = error_message
        run.details = details
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_latest_agent_run(self) -> Optional[AgentRun]:
        return self.db.query(AgentRun).order_by(desc(AgentRun.started_at)).first()

    # -------------------------------------------------------------
    # Logs
    # -------------------------------------------------------------
    def list_logs(
        self,
        level: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[int, List[LogEntry]]:
        query = self.db.query(LogEntry)
        if level and level.upper() != "ALL":
            query = query.filter(LogEntry.level == level.upper())
        if search:
            query = query.filter(LogEntry.message.ilike(f"%{search}%"))

        total = query.count()
        logs = query.order_by(desc(LogEntry.created_at)).offset(skip).limit(limit).all()
        return total, logs

    def clear_logs(self) -> None:
        self.db.query(LogEntry).delete()
        self.db.commit()
