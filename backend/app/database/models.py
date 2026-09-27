from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    picture = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    credentials = relationship("GoogleCredential", back_populates="user", cascade="all, delete-orphan")
    folders = relationship("DriveFolder", back_populates="user", cascade="all, delete-orphan")


class GoogleCredential(Base):
    __tablename__ = "google_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    scopes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="credentials")


class DriveFolder(Base):
    __tablename__ = "drive_folders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    folder_id = Column(String(255), unique=True, index=True, nullable=False)
    folder_name = Column(String(255), nullable=False)
    is_selected = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="folders")


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    drive_file_id = Column(String(255), unique=True, index=True, nullable=False)
    file_name = Column(String(512), nullable=False)
    mime_type = Column(String(128), default="video/mp4", nullable=False)
    size = Column(BigInteger, default=0, nullable=False)
    drive_folder_id = Column(String(255), nullable=True)
    status = Column(
        String(64),
        default="available",
        index=True,
        nullable=False,
    )  # available, downloading, processing, uploading, uploaded, failed
    local_path = Column(String(1024), nullable=True)
    duration = Column(Integer, nullable=True)  # in seconds
    resolution = Column(String(64), nullable=True)
    fps = Column(String(32), nullable=True)
    codec = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    uploads = relationship("Upload", back_populates="video", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="video")

    __table_args__ = (
        Index("ix_videos_status_drive_id", "status", "drive_file_id"),
    )


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    youtube_video_id = Column(String(128), index=True, nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON string of list[str]
    category_id = Column(String(32), default="20", nullable=False)
    privacy_status = Column(String(32), default="private", nullable=False)
    status = Column(
        String(64),
        default="pending",
        index=True,
        nullable=False,
    )  # pending, uploading, uploaded, failed
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    video = relationship("Video", back_populates="uploads")


class AgentSettings(Base):
    __tablename__ = "agent_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    enabled = Column(Boolean, default=False, nullable=False)
    interval_minutes = Column(Integer, default=360, nullable=False)  # default 6 hours
    privacy_status = Column(String(32), default="private", nullable=False)
    category_id = Column(String(32), default="20", nullable=False)
    generate_title = Column(Boolean, default=True, nullable=False)
    generate_description = Column(Boolean, default=True, nullable=False)
    generate_tags = Column(Boolean, default=True, nullable=False)
    ollama_model = Column(String(128), default="qwen3:8b", nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    delete_after_upload = Column(Boolean, default=True, nullable=False)
    fallback_if_ai_unavailable = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    status = Column(
        String(64),
        default="running",
        index=True,
        nullable=False,
    )  # running, success, failed, skipped
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    error_message = Column(Text, nullable=True)
    details = Column(Text, nullable=True)

    video = relationship("Video", back_populates="agent_runs")


class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(32), index=True, default="INFO", nullable=False)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True, nullable=False)
