import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session
from googleapiclient.discovery import build

from app.core.config import settings
from app.core.logging_config import logger
from app.database.repository import Repository
from app.services.google_auth_service import GoogleAuthService
from app.services.ai_service import AIService


# Global in-memory agent execution state for real-time debugging
AGENT_PIPELINE_STATE: Dict[str, Any] = {
    "status": "idle",
    "step_id": "idle",
    "step_label": "System Ready & Idle",
    "progress": 0,
    "current_video": None,
    "started_at": None,
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "logs": [],
    "last_result": None,
}


def update_agent_pipeline_state(
    status: str,
    step_id: str,
    step_label: str,
    progress: int,
    current_video: Optional[str] = None,
    log_message: Optional[str] = None,
    last_result: Optional[Dict[str, Any]] = None,
):
    """Update live agent state tracker for the debug console."""
    global AGENT_PIPELINE_STATE
    now_iso = datetime.now(timezone.utc).isoformat()
    AGENT_PIPELINE_STATE["status"] = status
    AGENT_PIPELINE_STATE["step_id"] = step_id
    AGENT_PIPELINE_STATE["step_label"] = step_label
    AGENT_PIPELINE_STATE["progress"] = progress
    AGENT_PIPELINE_STATE["updated_at"] = now_iso

    if current_video is not None:
        AGENT_PIPELINE_STATE["current_video"] = current_video

    if status == "running" and AGENT_PIPELINE_STATE["started_at"] is None:
        AGENT_PIPELINE_STATE["started_at"] = now_iso
    elif status in ["idle", "success", "error"]:
        AGENT_PIPELINE_STATE["started_at"] = None

    if last_result is not None:
        AGENT_PIPELINE_STATE["last_result"] = last_result

    if log_message:
        entry = {
            "timestamp": now_iso,
            "step": step_id,
            "message": log_message,
        }
        # Keep last 50 pipeline logs
        logs = AGENT_PIPELINE_STATE.get("logs", [])
        logs.append(entry)
        AGENT_PIPELINE_STATE["logs"] = logs[-50:]


class DebugService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = Repository(db)
        self.auth_service = GoogleAuthService(db)
        self.ai_service = AIService(db)

    def get_live_pipeline_state(self) -> Dict[str, Any]:
        """Return real-time agent pipeline state."""
        return AGENT_PIPELINE_STATE

    def get_system_diagnostics(self) -> Dict[str, Any]:
        """
        Run a deep health probe across all subsystems:
        OAuth, Drive, YouTube, Gemini AI, Ollama, Database, Storage, Scheduler.
        """
        diagnostics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "healthy",
            "subsystems": {},
        }

        # 1. Google OAuth Check
        try:
            auth_status = self.auth_service.get_auth_status()
            user = self.repo.get_user()
            cred_record = self.repo.get_credential()

            token_expires_in = None
            if cred_record and cred_record.token_expiry:
                expiry = cred_record.token_expiry
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                diff_seconds = int((expiry - now).total_seconds())
                token_expires_in = f"{max(0, diff_seconds // 60)} minutes"

            diagnostics["subsystems"]["google_oauth"] = {
                "status": "healthy" if auth_status["is_authenticated"] else "warning",
                "authenticated": auth_status["is_authenticated"],
                "email": user.email if user else None,
                "name": user.name if user else None,
                "token_expires_in": token_expires_in,
                "has_drive_scope": auth_status["has_drive_scope"],
                "has_youtube_scope": auth_status["has_youtube_scope"],
            }
        except Exception as e:
            diagnostics["subsystems"]["google_oauth"] = {
                "status": "error",
                "error": str(e),
            }

        # 2. Google Drive API Check
        try:
            creds = self.auth_service.get_credentials()
            if creds and creds.valid:
                drive_client = build("drive", "v3", credentials=creds, cache_discovery=False)
                about = drive_client.about().get(fields="user, storageQuota").execute()
                selected_folder = self.repo.get_selected_folder()
                folder_stats = self.repo.get_video_stats(selected_folder.folder_id if selected_folder else None)

                diagnostics["subsystems"]["google_drive"] = {
                    "status": "healthy",
                    "connected": True,
                    "selected_folder_name": selected_folder.folder_name if selected_folder else None,
                    "selected_folder_id": selected_folder.folder_id if selected_folder else None,
                    "indexed_videos": folder_stats.get("total", 0),
                    "unuploaded_videos": folder_stats.get("remaining", 0),
                    "storage_quota": about.get("storageQuota", {}),
                }
            else:
                diagnostics["subsystems"]["google_drive"] = {
                    "status": "disconnected",
                    "connected": False,
                    "message": "Google credentials not authenticated or expired.",
                }
        except Exception as e:
            diagnostics["subsystems"]["google_drive"] = {
                "status": "error",
                "connected": False,
                "error": str(e),
            }

        # 3. YouTube Data API Check
        try:
            creds = self.auth_service.get_credentials()
            if creds and creds.valid:
                youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
                channel_resp = youtube.channels().list(part="snippet,statistics", mine=True).execute()
                items = channel_resp.get("items", [])
                if items:
                    ch = items[0]
                    stats = ch.get("statistics", {})
                    snippet = ch.get("snippet", {})
                    diagnostics["subsystems"]["youtube_api"] = {
                        "status": "healthy",
                        "connected": True,
                        "channel_id": ch.get("id"),
                        "channel_title": snippet.get("title"),
                        "subscriber_count": stats.get("subscriberCount", "0"),
                        "video_count": stats.get("videoCount", "0"),
                        "view_count": stats.get("viewCount", "0"),
                    }
                else:
                    diagnostics["subsystems"]["youtube_api"] = {
                        "status": "warning",
                        "connected": True,
                        "message": "Authenticated, but no YouTube Channel associated with this Google Account.",
                    }
            else:
                diagnostics["subsystems"]["youtube_api"] = {
                    "status": "disconnected",
                    "connected": False,
                    "message": "YouTube API scopes not authorized.",
                }
        except Exception as e:
            diagnostics["subsystems"]["youtube_api"] = {
                "status": "error",
                "connected": False,
                "error": str(e),
            }

        # 4. Gemini AI Engine Check (with live ping & latency measurement)
        db_settings = self.repo.get_settings()
        gemini_api_key = self.ai_service.gemini_api_key
        gemini_model = self.ai_service.gemini_model
        gemini_img_model = getattr(db_settings, "gemini_image_model", "imagen-3.0-generate-002") or "imagen-3.0-generate-002"

        if gemini_api_key and not gemini_api_key.startswith("Option"):
            try:
                start_t = time.perf_counter()
                probe_url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_api_key}"
                payload = {
                    "contents": [{"parts": [{"text": "Reply with only the word OK"}]}],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 10},
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(probe_url, json=payload)
                    latency_ms = round((time.perf_counter() - start_t) * 1000, 1)

                if resp.status_code == 200:
                    diagnostics["subsystems"]["gemini_ai"] = {
                        "status": "healthy",
                        "connected": True,
                        "model": gemini_model,
                        "image_model": gemini_img_model,
                        "latency_ms": latency_ms,
                        "api_key_configured": True,
                        "api_key_masked": f"{gemini_api_key[:6]}...{gemini_api_key[-4:]}" if len(gemini_api_key) > 10 else "***",
                    }
                else:
                    diagnostics["subsystems"]["gemini_ai"] = {
                        "status": "error",
                        "connected": False,
                        "model": gemini_model,
                        "status_code": resp.status_code,
                        "error": resp.text[:200],
                        "api_key_configured": True,
                    }
            except Exception as e:
                diagnostics["subsystems"]["gemini_ai"] = {
                    "status": "error",
                    "connected": False,
                    "model": gemini_model,
                    "error": str(e),
                    "api_key_configured": True,
                }
        else:
            diagnostics["subsystems"]["gemini_ai"] = {
                "status": "warning",
                "connected": False,
                "model": gemini_model,
                "message": "Gemini API Key not set in Settings or .env.",
                "api_key_configured": False,
            }

        # 5. Ollama AI Check
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    diagnostics["subsystems"]["ollama_ai"] = {
                        "status": "healthy",
                        "connected": True,
                        "base_url": settings.OLLAMA_BASE_URL,
                        "models": models,
                    }
                else:
                    diagnostics["subsystems"]["ollama_ai"] = {
                        "status": "warning",
                        "connected": False,
                        "base_url": settings.OLLAMA_BASE_URL,
                    }
        except Exception:
            diagnostics["subsystems"]["ollama_ai"] = {
                "status": "offline",
                "connected": False,
                "base_url": settings.OLLAMA_BASE_URL,
            }

        # 6. Database Health & Table Metrics
        try:
            total_videos, _ = self.repo.list_videos(limit=1)
            total_uploads, _ = self.repo.list_uploads(limit=1)
            total_logs, _ = self.repo.list_logs(limit=1)

            db_size_kb = 0
            if os.path.exists("./data/agent.db"):
                db_size_kb = round(os.path.getsize("./data/agent.db") / 1024, 1)

            diagnostics["subsystems"]["database"] = {
                "status": "healthy",
                "database_engine": "SQLite",
                "db_size_kb": db_size_kb,
                "counts": {
                    "videos": total_videos,
                    "uploads": total_uploads,
                    "logs": total_logs,
                },
            }
        except Exception as e:
            diagnostics["subsystems"]["database"] = {
                "status": "error",
                "error": str(e),
            }

        # 7. File Storage Subsystem
        try:
            dirs = {
                "downloads": settings.DOWNLOAD_DIRECTORY,
                "thumbnails": settings.THUMBNAIL_DIRECTORY,
                "logs": settings.LOG_DIRECTORY,
            }
            storage_info = {}
            for k, d in dirs.items():
                os.makedirs(d, exist_ok=True)
                file_count = len(os.listdir(d))
                storage_info[k] = {"path": d, "file_count": file_count, "accessible": True}

            diagnostics["subsystems"]["local_storage"] = {
                "status": "healthy",
                "directories": storage_info,
            }
        except Exception as e:
            diagnostics["subsystems"]["local_storage"] = {
                "status": "error",
                "error": str(e),
            }

        # 8. Background Scheduler Subsystem
        try:
            from app.services.scheduler_service import SchedulerService
            scheduler_status = SchedulerService.get_status()
            diagnostics["subsystems"]["scheduler"] = {
                "status": "healthy" if scheduler_status.get("scheduler_running") else "warning",
                "scheduler_running": scheduler_status.get("scheduler_running", False),
                "is_job_executing": scheduler_status.get("is_job_currently_executing", False),
                "job_active": scheduler_status.get("job_active", False),
                "next_scheduled_run": scheduler_status.get("next_scheduled_run"),
                "interval_minutes": db_settings.interval_minutes,
                "agent_enabled": db_settings.enabled,
            }
        except Exception as e:
            diagnostics["subsystems"]["scheduler"] = {
                "status": "error",
                "error": str(e),
            }

        return diagnostics

    def simulate_ai_pipeline(self, test_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulate the AI reasoning process for a given video title (or the next unuploaded video)
        without uploading or mutating files.
        """
        if not test_title:
            selected_folder = self.repo.get_selected_folder()
            if selected_folder:
                video = self.repo.select_random_unuploaded_video(selected_folder.folder_id)
                if video:
                    test_title = video.file_name

        if not test_title:
            test_title = "Unity Game Development Character Customization Tutorial"

        start_time = time.perf_counter()
        meta = {"duration": 120, "resolution": "1920x1080", "fps": "60.0", "codec": "h264"}

        # 1. Generate Title
        gen_title = self.ai_service.generate_title(test_title, meta)

        # 2. Generate Description
        gen_description = self.ai_service.generate_description(gen_title, test_title, meta)

        # 3. Generate Tags
        gen_tags = self.ai_service.generate_tags(gen_title, gen_description, test_title)

        # 4. Generate Thumbnail Visual Prompt
        thumbnail_prompt = f"16:9 YouTube video thumbnail for '{gen_title}'. Cinematic lighting, vibrant colors, 4k ultra-detailed."

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)

        db_settings = self.repo.get_settings()

        return {
            "input_file_name": test_title,
            "provider": getattr(db_settings, "ai_provider", "gemini"),
            "model": self.ai_service.gemini_model,
            "image_model": getattr(db_settings, "gemini_image_model", "imagen-3.0-generate-002"),
            "generated_title": gen_title,
            "generated_description": gen_description,
            "generated_tags": gen_tags,
            "thumbnail_prompt": thumbnail_prompt,
            "execution_time_ms": elapsed_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
