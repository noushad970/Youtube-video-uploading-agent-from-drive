import base64
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
            app_settings = self.repo.get_settings()
            return settings.OLLAMA_BASE_URL
        return settings.OLLAMA_BASE_URL

    @property
    def model(self) -> str:
        if self.repo:
            app_settings = self.repo.get_settings()
            return app_settings.ollama_model or settings.OLLAMA_MODEL
        return settings.OLLAMA_MODEL

    @property
    def ai_provider(self) -> str:
        if self.repo:
            app_settings = self.repo.get_settings()
            if getattr(app_settings, "ai_provider", None):
                return app_settings.ai_provider
        return settings.AI_PROVIDER or "gemini"

    @property
    def gemini_model(self) -> str:
        if self.repo:
            app_settings = self.repo.get_settings()
            if getattr(app_settings, "gemini_model", None):
                return app_settings.gemini_model
        return settings.GEMINI_MODEL or "gemini-2.5-flash"

    @property
    def gemini_api_key(self) -> str:
        if self.repo:
            app_settings = self.repo.get_settings()
            if getattr(app_settings, "gemini_api_key", None):
                return app_settings.gemini_api_key
        return settings.GEMINI_API_KEY or ""

    @property
    def gemini_image_model(self) -> str:
        if self.repo:
            app_settings = self.repo.get_settings()
            if getattr(app_settings, "gemini_image_model", None):
                return app_settings.gemini_image_model
        return settings.GEMINI_IMAGE_MODEL or "imagen-3.0-generate-002"

    def check_health(self) -> Dict[str, Any]:
        """Check AI service readiness for Gemini and local Ollama."""
        has_gemini_key = bool(self.gemini_api_key)
        ollama_connected = False
        ollama_models = []
        try:
            with httpx.Client(timeout=3) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    ollama_models = [m.get("name") for m in data.get("models", [])]
                    ollama_connected = True
        except Exception:
            pass

        return {
            "active_provider": self.ai_provider,
            "gemini_ready": has_gemini_key,
            "gemini_model": self.gemini_model,
            "ollama_connected": ollama_connected,
            "ollama_model": self.model,
            "available_ollama_models": ollama_models,
        }

    def _call_gemini(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """Send prompt to Google Gemini Generative Language API."""
        api_key = self.gemini_api_key
        if not api_key:
            return None

        model = self.gemini_model or "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
            },
        }

        try:
            with httpx.Client(timeout=45) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
                else:
                    logger.warning(f"Gemini API returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Gemini request failed: {e}")
        return None

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

    def _call_ai(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """Unified AI dispatcher: Uses Gemini or Ollama based on configuration and availability."""
        if self.ai_provider == "gemini" and self.gemini_api_key:
            res = self._call_gemini(prompt, temperature)
            if res:
                return res
            logger.info("Gemini call yielded no response. Trying local Ollama fallback...")

        # Default or fallback to Ollama
        ollama_res = self._call_ollama(prompt, temperature)
        if ollama_res:
            return ollama_res

        # If Ollama failed and Gemini key exists, try Gemini
        if self.gemini_api_key and self.ai_provider != "gemini":
            return self._call_gemini(prompt, temperature)

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
            ai_response = self._call_ai(prompt, temperature=0.6)
            if ai_response:
                clean_title = ai_response.strip().strip('"').strip("'").strip()
                clean_title = re.sub(r"^(Title\s*:\s*|\*\*Title\s*:\s*\*\*)", "", clean_title, flags=re.IGNORECASE)
                if len(clean_title) > 100:
                    clean_title = clean_title[:97] + "..."
                if clean_title:
                    return clean_title
        except Exception as e:
            logger.warning(f"Failed to generate title with AI: {e}")

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
            ai_response = self._call_ai(prompt, temperature=0.7)
            if ai_response:
                return ai_response.strip()
        except Exception as e:
            logger.warning(f"Failed to generate description with AI: {e}")

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
            ai_response = self._call_ai(prompt, temperature=0.5)
            if ai_response:
                match = re.search(r"\{.*\}", ai_response, re.DOTALL)
                json_str = match.group(0) if match else ai_response
                data = json.loads(json_str)
                tags = data.get("tags", [])
                if isinstance(tags, list):
                    clean_tags = [str(t).strip().lower() for t in tags if str(t).strip()]
                    return clean_tags[:15]
        except Exception as e:
            logger.warning(f"Failed to generate tags with AI or parse JSON: {e}")

        return []

    def generate_thumbnail(
        self,
        title: str,
        file_name: str,
        video_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a high-CTR 16:9 YouTube video thumbnail using Google Gemini Imagen 3 API
        directly aligned with the video's title.
        Saves JPEG to THUMBNAIL_DIRECTORY and returns local filepath.
        """
        api_key = self.gemini_api_key
        if not api_key:
            logger.info("Gemini API key is not set. Skipping AI thumbnail generation.")
            return None

        clean_title = self._clean_filename_to_title(file_name)
        subject = title if title and len(title) > 3 else clean_title

        # Step 1: Craft an optimized visual prompt for Imagen 3
        visual_prompt = (
            f"Vibrant, eye-catching, professional YouTube video thumbnail representing '{subject}'. "
            "High contrast, bold focal subject, cinematic lighting, 4k ultra-detailed, 16:9 widescreen composition."
        )

        try:
            prompt_req = (
                f"In 1-2 concise sentences, describe a visually stunning, high-CTR YouTube video thumbnail for a video titled: '{subject}'. "
                "Include key visual elements, dramatic colors, lighting, and clean composition without text overlay."
            )
            ai_crafted_prompt = self._call_gemini(prompt_req, temperature=0.7)
            if ai_crafted_prompt and len(ai_crafted_prompt) > 20:
                visual_prompt = ai_crafted_prompt.strip().strip('"').strip("'")
                logger.info(f"AI Crafted Thumbnail Visual Prompt: {visual_prompt}")
        except Exception as e:
            logger.debug(f"Visual prompt enhancement skipped: {e}")

        # Step 2: Request 16:9 Image from Google Imagen 3
        model = self.gemini_image_model or "imagen-3.0-generate-002"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}"
        payload = {
            "instances": [{"prompt": visual_prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "16:9",
                "outputMimeType": "image/jpeg",
            },
        }

        try:
            logger.info(f"Generating AI thumbnail from Imagen 3 for '{subject}'...")
            with httpx.Client(timeout=60) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    predictions = data.get("predictions", [])
                    if predictions and "bytesBase64Encoded" in predictions[0]:
                        b64_bytes = predictions[0]["bytesBase64Encoded"]
                        img_data = base64.b64decode(b64_bytes)

                        # Save to thumbnail directory
                        thumb_dir = Path(settings.THUMBNAIL_DIRECTORY)
                        thumb_dir.mkdir(parents=True, exist_ok=True)
                        safe_stem = re.sub(r"[^\w\-]", "_", Path(file_name).stem)[:40]
                        identifier = video_id[:8] if video_id else "gen"
                        out_path = thumb_dir / f"thumb_{safe_stem}_{identifier}.jpg"
                        out_path.write_bytes(img_data)

                        logger.info(f"AI Thumbnail generated successfully and saved to: {out_path}")
                        return str(out_path.resolve())
                    else:
                        logger.warning(f"Gemini Imagen response missing image data: {data}")
                else:
                    logger.warning(f"Gemini Imagen API error {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail with Gemini Imagen API: {e}")

        return None

    def _clean_filename_to_title(self, file_name: str) -> str:
        """Convert a filename like 'epic_gameplay_part_1.mp4' to 'Epic Gameplay Part 1'."""
        name = Path(file_name).stem
        name = re.sub(r"[_\-\.]+", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name.title()[:100] if name else "Untitled Video"
