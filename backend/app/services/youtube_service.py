from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.database.repository import Repository
from app.services.google_auth_service import GoogleAuthService


class YouTubeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = Repository(db)
        self.auth_service = GoogleAuthService(db)

    def _get_youtube_client(self):
        """Construct authorized YouTube Data API v3 client."""
        credentials = self.auth_service.get_valid_credentials()
        if not credentials:
            raise PermissionError("Not authenticated with Google. Please connect your Google account.")
        return build("youtube", "v3", credentials=credentials, cache_discovery=False)

    def get_channel_info(self) -> Dict[str, Any]:
        """Fetch primary channel information for the authorized user."""
        service = self._get_youtube_client()
        response = (
            service.channels()
            .list(part="snippet,statistics,contentDetails", mine=True)
            .execute()
        )
        items = response.get("items", [])
        if not items:
            raise ValueError("No YouTube channel found associated with this Google account.")

        channel = items[0]
        snippet = channel.get("snippet", {})
        statistics = channel.get("statistics", {})

        return {
            "id": channel.get("id"),
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "custom_url": snippet.get("customUrl"),
            "published_at": snippet.get("publishedAt"),
            "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url"),
            "subscriber_count": statistics.get("subscriberCount", "0"),
            "video_count": statistics.get("videoCount", "0"),
            "view_count": statistics.get("viewCount", "0"),
        }

    def upload_video(
        self,
        file_path: str | Path,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        category_id: str = "20",
        privacy_status: str = "private",
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """
        Upload video file to YouTube via Resumable Media Upload.
        Returns YouTube Video ID.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Local video file not found at: {path}")

        service = self._get_youtube_client()

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags or [],
                "categoryId": category_id or "20",
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        # Resumable upload chunk size: 10MB
        media = MediaFileUpload(
            str(path),
            mimetype="video/*",
            resumable=True,
            chunksize=10 * 1024 * 1024,
        )

        logger.info(f"Initiating YouTube resumable upload for '{title}' (Privacy: {privacy_status})...")
        insert_request = service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                progress_pct = int(status.progress() * 100)
                if progress_callback:
                    progress_callback(int(status.resumable_progress), int(status.total_size))
                if progress_pct % 20 == 0:
                    logger.info(f"Uploading to YouTube: {progress_pct}%")

        youtube_id = response.get("id")
        if not youtube_id:
            raise ValueError(f"YouTube upload response did not include video ID: {response}")

        logger.info(f"YouTube upload successful! Video ID: {youtube_id}")
        return youtube_id

    def set_thumbnail(self, youtube_video_id: str, thumbnail_path: str | Path) -> bool:
        """Upload custom thumbnail for a YouTube video."""
        path = Path(thumbnail_path)
        if not path.exists():
            return False

        try:
            service = self._get_youtube_client()
            media = MediaFileUpload(str(path), mimetype="image/jpeg", resumable=False)
            service.thumbnails().set(videoId=youtube_video_id, media_body=media).execute()
            logger.info(f"Thumbnail uploaded for YouTube video {youtube_video_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to set custom thumbnail for {youtube_video_id}: {e}")
            return False

    def get_video_details(self, youtube_video_id: str) -> Optional[Dict[str, Any]]:
        """Fetch details for a specific uploaded YouTube video."""
        try:
            service = self._get_youtube_client()
            res = service.videos().list(part="snippet,status,statistics", id=youtube_video_id).execute()
            items = res.get("items", [])
            return items[0] if items else None
        except Exception as e:
            logger.warning(f"Failed to get video details for {youtube_video_id}: {e}")
            return None
