import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import logger
from app.database.repository import Repository
from app.database.models import Video


class AIService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.repo = Repository(db) if db else None

    @property
    def base_url(self) -> str:
        if self.repo:
            # Check if model/url overridden in database settings
            app_settings = self.repo.get_settings()
            return settings.OLLAMA_BASE_URL
        return settings.OLLAMA_BASE_URL

    @property
    def model(self) -> str:
        if self.repo:
            app_settings = self.repo.get_settings()
            return app_settings.ollama_model or settings.OLLAMA_MODEL
        return settings.OLLAMA_MODEL

    def check_health(self) -> Dict[str, Any]:
        """Check if local Ollama instance is reachable and list loaded models."""
        try:
            with httpx.Client(timeout=5) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    model_found = any(self.model in m for m in models)
                    return {
                        "connected": True,
                        "base_url": self.base_url,
                        "current_model": self.model,
                        "model_available": model_found,
                        "available_models": models,
                    }
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")

        return {
            "connected": False,
            "base_url": self.base_url,
            "current_model": self.model,
            "model_available": False,
            "available_models": [],
        }

    def _call_ollama(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """Send prompt to Ollama /api/generate endpoint."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        try:
            with httpx.Client(timeout=60) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("response", "").strip()
                else:
                    logger.warning(f"Ollama returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Ollama request failed: {e}")
        return None

    def generate_title(self, file_name: str, video_meta: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a concise, human-friendly YouTube title (max 100 characters).
        Falls back to formatted filename if AI generation fails.
        """
        fallback_title = self._clean_filename_to_title(file_name)
        prompt = f"""You are an expert YouTube metadata assistant.
Based on the following video file information, generate a concise, engaging, and accurate YouTube video title.
Video Filename: {file_name}
Duration: {video_meta.get('duration', 'unknown') if video_meta else 'unknown'} seconds
Resolution: {video_meta.get('resolution', 'unknown') if video_meta else 'unknown'}

Requirements:
- Maximum 95 characters.
- Do not use clickbait or misleading claims.
- Do not invent fictional events unsupported by the file name.
- Return ONLY the final title text, without quotes, explanations, or prefixes.
"""
        try:
            ai_response = self._call_ollama(prompt, temperature=0.6)
            if ai_response:
                clean_title = ai_response.strip().strip('"').strip("'").strip()
                # Remove common AI prefixes like 'Title:'
                clean_title = re.sub(r"^(Title\s*:\s*|\*\*Title\s*:\s*\*\*)", "", clean_title, flags=re.IGNORECASE)
                if len(clean_title) > 100:
                    clean_title = clean_title[:97] + "..."
                if clean_title:
                    return clean_title
        except Exception as e:
            logger.warning(f"Failed to generate title with Ollama: {e}")

        return fallback_title

    def generate_description(
        self,
        title: str,
        file_name: str,
        video_meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a YouTube video description with short introduction and hashtags.
        Falls back to a clean default description if AI is unavailable.
        """
        fallback_desc = f"{title}\n\nUploaded automatically via YouTube AI Upload Agent."
        prompt = f"""You are a YouTube metadata assistant.
Generate a clean, professional YouTube description for a video.
Title: {title}
Filename: {file_name}

Requirements:
- Write a short 2-3 sentence introduction explaining the video topic.
- Add 3 to 5 relevant hashtags at the bottom (e.g. #Gaming #Highlights).
- Do not make false promises or invent nonexistent claims.
- Return only the description text.
"""
        try:
            ai_response = self._call_ollama(prompt, temperature=0.7)
            if ai_response:
                return ai_response.strip()
        except Exception as e:
            logger.warning(f"Failed to generate description with Ollama: {e}")

        return fallback_desc

    def generate_tags(self, title: str, description: str, file_name: str) -> List[str]:
        """
        Generate 5 to 15 relevant YouTube tags in JSON format.
        Falls back to empty list on failure.
        """
        prompt = f"""Generate 5 to 15 relevant YouTube video search tags for this video.
Title: {title}
Filename: {file_name}

Requirements:
- Return ONLY valid JSON format:
{{"tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]}}
- Do not include markdown code blocks or explanations.
"""
        try:
            ai_response = self._call_ollama(prompt, temperature=0.5)
            if ai_response:
                # Extract JSON if enclosed in markdown code fences
                match = re.search(r"\{.*\}", ai_response, re.DOTALL)
                json_str = match.group(0) if match else ai_response
                data = json.loads(json_str)
                tags = data.get("tags", [])
                if isinstance(tags, list):
                    clean_tags = [str(t).strip().lower() for t in tags if str(t).strip()]
                    return clean_tags[:15]
        except Exception as e:
            logger.warning(f"Failed to generate tags with Ollama or parse JSON: {e}")

        return []

    def _clean_filename_to_title(self, file_name: str) -> str:
        """Convert a filename like 'epic_gameplay_part_1.mp4' to 'Epic Gameplay Part 1'."""
        name = Path(file_name).stem
        name = re.sub(r"[_\-\.]+", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name.title()[:100] if name else "Untitled Video"
