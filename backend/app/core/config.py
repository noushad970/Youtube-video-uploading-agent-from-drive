from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Google OAuth
    GOOGLE_CLIENT_ID: str = Field(default="", description="Google OAuth 2.0 Client ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="", description="Google OAuth 2.0 Client Secret")
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:8000/api/auth/google/callback",
        description="OAuth callback URL",
    )
    GOOGLE_SCOPES: List[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
    ]

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./data/agent.db",
        description="SQLAlchemy database URL",
    )

    # Ollama AI
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Local Ollama service URL",
    )
    OLLAMA_MODEL: str = Field(
        default="qwen3:8b",
        description="Default LLM model name for metadata generation",
    )

    # Storage Paths
    DOWNLOAD_DIRECTORY: str = Field(default="./data/videos", description="Temporary video download directory")
    THUMBNAIL_DIRECTORY: str = Field(default="./data/thumbnails", description="Thumbnail storage directory")
    LOG_DIRECTORY: str = Field(default="./data/logs", description="Log files directory")

    # Agent & Upload Defaults
    MAX_RETRIES: int = Field(default=3, ge=1, le=10, description="Max upload retry attempts")
    DEFAULT_PRIVACY_STATUS: str = Field(default="private", description="private, unlisted, or public")
    DEFAULT_CATEGORY_ID: str = Field(default="20", description="Default YouTube Category ID (20 = Gaming)")
    DELETE_AFTER_UPLOAD: bool = Field(default=True, description="Delete local file after successful upload")
    FALLBACK_IF_AI_UNAVAILABLE: bool = Field(
        default=True,
        description="Fallback to filename and simple description if Ollama fails",
    )

    # Security
    SECRET_KEY: str = Field(
        default="youtube-agent-secret-encryption-key-32-chars-min-len",
        description="Key used for local token encryption at rest",
    )

    # Server & Networking
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    def ensure_directories(self) -> None:
        """Ensure all required data directories exist."""
        for path_str in [self.DOWNLOAD_DIRECTORY, self.THUMBNAIL_DIRECTORY, self.LOG_DIRECTORY]:
            Path(path_str).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
