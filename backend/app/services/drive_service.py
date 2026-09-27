import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.database.repository import Repository
from app.services.google_auth_service import GoogleAuthService
from app.utils.file_utils import sanitize_filename, check_disk_space, format_bytes

SUPPORTED_MIME_TYPES = [
    "video/mp4",
    "video/quicktime",
    "video/x-matroska",
    "video/webm",
    "video/x-msvideo",
    "video/avi",
    "video/mpeg",
    "video/3gpp",
]

SUPPORTED_EXTENSIONS = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".flv", ".wmv")


class DriveService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = Repository(db)
        self.auth_service = GoogleAuthService(db)

    def _get_drive_client(self):
        """Construct authorized Google Drive API client."""
        credentials = self.auth_service.get_valid_credentials()
        if not credentials:
            raise PermissionError("Not authenticated with Google. Please authenticate first.")
        return build("drive", "v3", credentials=credentials, cache_discovery=False)

    def list_drive_folders(self) -> List[Dict[str, Any]]:
        """List all accessible Google Drive folders for the user."""
        service = self._get_drive_client()
        query = "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        
        folders = []
        page_token = None
        while True:
            response = (
                service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="nextPageToken, files(id, name, modifiedTime)",
                    pageToken=page_token,
                    pageSize=100,
                )
                .execute()
            )
            for file in response.get("files", []):
                folders.append({
                    "folder_id": file.get("id"),
                    "folder_name": file.get("name"),
                })
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return folders

    def list_videos(self, folder_id: str) -> List[Dict[str, Any]]:
        """List all video files inside a specific Google Drive folder."""
        service = self._get_drive_client()
        query = f"'{folder_id}' in parents and trashed = false"
        
        videos = []
        page_token = None
        while True:
            response = (
                service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)",
                    pageToken=page_token,
                    pageSize=100,
                )
                .execute()
            )
            for file in response.get("files", []):
                mime = file.get("mimeType", "")
                name = file.get("name", "")
                # Check MIME type or file extension
                is_video = (
                    mime.startswith("video/")
                    or mime in SUPPORTED_MIME_TYPES
                    or name.lower().endswith(SUPPORTED_EXTENSIONS)
                )
                if is_video:
                    videos.append({
                        "drive_file_id": file.get("id"),
                        "file_name": name,
                        "mime_type": mime or "video/mp4",
                        "size": int(file.get("size", 0)),
                    })

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return videos

    def get_video_metadata(self, file_id: str) -> Dict[str, Any]:
        """Fetch file metadata for a specific Drive file."""
        service = self._get_drive_client()
        file = (
            service.files()
            .get(
                fileId=file_id,
                fields="id, name, mimeType, size, videoMediaMetadata, modifiedTime",
            )
            .execute()
        )
        return {
            "drive_file_id": file.get("id"),
            "file_name": file.get("name"),
            "mime_type": file.get("mimeType"),
            "size": int(file.get("size", 0)),
            "media_metadata": file.get("videoMediaMetadata", {}),
        }

    def sync_folder_videos(self, folder_id: str, folder_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scan drive folder and synchronize metadata with database.
        Returns the list of found videos.
        """
        if not folder_name:
            try:
                service = self._get_drive_client()
                f = service.files().get(fileId=folder_id, fields="name").execute()
                folder_name = f.get("name", "Unknown Folder")
            except Exception:
                folder_name = "Selected Folder"

        self.repo.select_folder(folder_id=folder_id, folder_name=folder_name)
        drive_videos = self.list_videos(folder_id)

        for v in drive_videos:
            self.repo.upsert_video_from_drive(
                drive_file_id=v["drive_file_id"],
                file_name=v["file_name"],
                mime_type=v["mime_type"],
                size=v["size"],
                folder_id=folder_id,
            )

        logger.info(
            f"Synced Drive folder '{folder_name}' ({folder_id}): found {len(drive_videos)} videos"
        )
        return drive_videos

    def download_video(
        self,
        file_id: str,
        destination_path: str | Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Path:
        """
        Download a video file from Google Drive to local destination path in chunks.
        """
        dest = Path(destination_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        service = self._get_drive_client()
        file_meta = service.files().get(fileId=file_id, fields="size, name").execute()
        file_size = int(file_meta.get("size", 0))

        # Check local disk space
        if file_size > 0 and not check_disk_space(file_size, str(dest.parent)):
            raise IOError(f"Insufficient local disk space to download video ({format_bytes(file_size)})")

        logger.info(f"Starting download for {file_meta.get('name')} ({format_bytes(file_size)}) -> {dest}")

        request = service.files().get_media(fileId=file_id)
        with io.FileIO(str(dest), "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=10 * 1024 * 1024)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress_pct = int(status.progress() * 100)
                    if progress_callback:
                        progress_callback(int(status.resumable_progress), file_size)
                    if progress_pct % 25 == 0:
                        logger.info(f"Downloading {dest.name}: {progress_pct}%")

        logger.info(f"Finished downloading video: {dest}")
        return dest
