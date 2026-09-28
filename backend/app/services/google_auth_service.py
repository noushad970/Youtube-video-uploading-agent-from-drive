import json
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import logger
from app.database.repository import Repository
from app.database.models import GoogleCredential, User


class GoogleAuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = Repository(db)

    def _get_client_config(self) -> Dict[str, Any]:
        """Generate client configuration dictionary for Google OAuth Flow."""
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError(
                "Google OAuth credentials missing. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
            )
        return {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        }

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Create OAuth 2.0 authorization URL for user consent."""
        client_config = self._get_client_config()
        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=settings.GOOGLE_SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
            autogenerate_code_verifier=False,
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
            state=state,
        )
        return auth_url

    def handle_auth_callback(self, code: str) -> Tuple[User, GoogleCredential]:
        """Exchange authorization code for credentials and store them securely."""
        client_config = self._get_client_config()
        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=settings.GOOGLE_SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
            autogenerate_code_verifier=False,
        )
        flow.fetch_token(code=code)
        credentials: Credentials = flow.credentials

        # Fetch profile info using credentials
        user_info = self._fetch_user_info(credentials)
        email = user_info.get("email")
        if not email:
            raise ValueError("Unable to retrieve email from Google OAuth response")

        user = self.repo.upsert_user(
            email=email,
            name=user_info.get("name"),
            picture=user_info.get("picture"),
        )

        scopes_str = " ".join(credentials.scopes) if credentials.scopes else " ".join(settings.GOOGLE_SCOPES)
        token_expiry = credentials.expiry
        if token_expiry and token_expiry.tzinfo is None:
            token_expiry = token_expiry.replace(tzinfo=timezone.utc)

        cred_record = self.repo.save_credential(
            user_id=user.id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expiry=token_expiry,
            scopes=scopes_str,
        )

        logger.info(f"Successfully authenticated Google user: {email}")
        return user, cred_record

    def _fetch_user_info(self, credentials: Credentials) -> Dict[str, Any]:
        """Query Google userinfo endpoint using access token."""
        try:
            with httpx.Client(timeout=10) as client:
                res = client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {credentials.token}"},
                )
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning(f"Error fetching userinfo from Google: {e}")
        return {}

    def get_valid_credentials(self, user_id: Optional[int] = None) -> Optional[Credentials]:
        """
        Retrieve credentials, automatically refreshing them if expired.
        Updates refreshed tokens back to database.
        """
        cred_record = self.repo.get_credential(user_id)
        if not cred_record or not cred_record.access_token:
            return None

        client_config = self._get_client_config()
        web_cfg = client_config["web"]

        scopes = cred_record.scopes.split() if cred_record.scopes else settings.GOOGLE_SCOPES

        credentials = Credentials(
            token=getattr(cred_record, "decrypted_access_token", cred_record.access_token),
            refresh_token=getattr(cred_record, "decrypted_refresh_token", cred_record.refresh_token),
            token_uri=web_cfg["token_uri"],
            client_id=web_cfg["client_id"],
            client_secret=web_cfg["client_secret"],
            scopes=scopes,
            expiry=cred_record.token_expiry,
        )

        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            try:
                logger.info("Refreshing expired Google OAuth access token...")
                credentials.refresh(Request())
                token_expiry = credentials.expiry
                if token_expiry and token_expiry.tzinfo is None:
                    token_expiry = token_expiry.replace(tzinfo=timezone.utc)

                self.repo.save_credential(
                    user_id=cred_record.user_id,
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token,
                    token_expiry=token_expiry,
                    scopes=" ".join(credentials.scopes or scopes),
                )
                logger.info("Successfully refreshed Google OAuth token")
            except Exception as e:
                logger.error(f"Failed to refresh Google OAuth token: {e}")
                return None

        return credentials

    def get_auth_status(self) -> Dict[str, Any]:
        """Get current Google connection status and available scopes."""
        user = self.repo.get_user()
        cred_record = self.repo.get_credential()

        if not user or not cred_record or not cred_record.access_token:
            return {
                "is_authenticated": False,
                "email": None,
                "name": None,
                "picture": None,
                "token_expiry": None,
                "scopes": None,
                "has_drive_scope": False,
                "has_youtube_scope": False,
            }

        scopes_str = cred_record.scopes or ""
        has_drive = "drive" in scopes_str
        has_youtube = "youtube" in scopes_str

        return {
            "is_authenticated": True,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "token_expiry": cred_record.token_expiry,
            "scopes": scopes_str,
            "has_drive_scope": has_drive,
            "has_youtube_scope": has_youtube,
        }

    def disconnect(self) -> bool:
        """Revoke token with Google API and clear credentials from database."""
        cred_record = self.repo.get_credential()
        if cred_record and cred_record.access_token:
            token = getattr(cred_record, "decrypted_access_token", cred_record.access_token)
            try:
                with httpx.Client(timeout=10) as client:
                    client.post(
                        "https://oauth2.googleapis.com/revoke",
                        params={"token": token},
                        headers={"content-type": "application/x-www-form-urlencoded"},
                    )
            except Exception as e:
                logger.warning(f"Failed to revoke Google token on server: {e}")

        self.repo.delete_all_credentials()
        logger.info("Google account disconnected and credentials cleared")
        return True
