import base64
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import logger
from app.database.repository import Repository
from app.database.models import Video
from app.utils.video_utils import extract_and_enhance_thumbnail, create_graphic_thumbnail


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
        model = None
        if self.repo:
            app_settings = self.repo.get_settings()
            if getattr(app_settings, "gemini_model", None):
                model = app_settings.gemini_model
        if not model:
            model = settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
        # Strict safeguard: Never use models lower than 3.5 (discontinued and return 404)
        if any(old in model.lower() for old in ["2.5", "1.5", "1.0", "gemini-pro", "gemini-flash-latest"]):
            logger.info(f"Auto-upgrading legacy Gemini model '{model}' to 'gemini-3.5-flash-lite'")
            return "gemini-3.5-flash-lite"
        return model

    @property
    def gemini_api_key(self) -> str:
        key = None
        if self.repo:
            app_settings = self.repo.get_settings()
            candidate = getattr(app_settings, "gemini_api_key", None)
            if candidate and not candidate.startswith("Option") and len(candidate.strip()) > 10:
                key = candidate.strip()
        if not key:
            key = (settings.GEMINI_API_KEY or "").strip()
        return key

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

        model = self.gemini_model or "gemini-3.5-flash-lite"
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
        prompt = f"""You are an expert YouTube title strategist.
Based on the following video file information, generate a concise, engaging, and accurate YouTube video title.
Video Filename: {file_name}
Duration: {video_meta.get('duration', 'unknown') if video_meta else 'unknown'} seconds
Resolution: {video_meta.get('resolution', 'unknown') if video_meta else 'unknown'}

Requirements:
- Maximum 90 characters.
- Engaging, professional, and directly describes the content.
- Do not use clickbait or misleading claims.
- Return ONLY the final title text, without quotes, explanations, or prefixes like "Title:".
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
        Generate a comprehensive, detailed, long-form YouTube video description (350-600+ words).
        Includes overview & hook, what viewers will learn, chapter breakdown placeholders,
        pro-tips, call to action, and search-optimized hashtags.
        Falls back to a rich structured long description if AI is unavailable.
        """
        clean_name = self._clean_filename_to_title(file_name)
        fallback_desc = f"""{title}

Welcome to this video! In this session, we take an in-depth, hands-on look at {clean_name}. Whether you are just getting started or looking to elevate your skills, this video walks you through the essential concepts, workflow, and techniques you need to succeed.

📌 WHAT YOU WILL LEARN IN THIS VIDEO:
• Comprehensive overview and breakdown of {clean_name}
• Step-by-step walkthrough of core mechanics and setup
• Key techniques, best practices, and performance tips
• How to troubleshoot common challenges and optimize your workflow

⏱️ CHAPTERS & TIMESTAMPS:
0:00 - Introduction & Overview
0:35 - Key Concepts & Initial Setup
1:20 - Step-by-Step Walkthrough
2:15 - Pro Tips & Optimization Best Practices
2:50 - Summary & Next Steps

💡 VALUABLE TAKEAWAYS:
Take your knowledge to the next level by following along with each step. Experiment with different settings and customize the process to fit your unique style and project goals!

🔔 ENJOYED THE VIDEO?
If you found this video helpful, please give it a thumbs up 👍, share it with others, and hit the SUBSCRIBE button with the notification bell 🔔 turned on so you never miss another upload!

Drop a comment below with your thoughts, questions, or suggestions for what you'd like to see next!

#Tutorial #Gaming #GameDev #Tech #Walkthrough #HowTo #VideoGuide #TipsAndTricks
"""
        prompt = f"""You are a professional YouTube SEO and metadata expert.
Generate a comprehensive, detailed, and engaging LONG-FORM YouTube video description for the following video:

Video Title: {title}
Filename: {file_name}
Duration: {video_meta.get('duration', 'unknown') if video_meta else 'unknown'} seconds
Resolution: {video_meta.get('resolution', 'unknown') if video_meta else 'unknown'}

The user specifically requested a LONG, thorough description (350-600 words). Include the following sections:
1. HOOK & OVERVIEW (2-3 detailed, descriptive paragraphs explaining the video topic, context, and why it is interesting/valuable to watch).
2. WHAT YOU WILL LEARN / KEY HIGHLIGHTS (4-6 detailed bullet points explaining specific takeaways).
3. CHAPTERS / TIMESTAMPS (Provide a realistic chapter breakdown starting with 0:00 Introduction).
4. PRO TIPS & BEST PRACTICES (2-3 actionable tips related to the video subject).
5. CALL TO ACTION & ENGAGEMENT (Encourage viewers to Like, Subscribe, click the notification bell, and leave a comment).
6. SEARCH-OPTIMIZED HASHTAGS (6 to 10 relevant hashtags at the very bottom, e.g. #Gaming #Tutorial #Tech).

Return ONLY the complete description text. Do not wrap in markdown code blocks or add prefixes.
"""
        try:
            ai_response = self._call_ai(prompt, temperature=0.7)
            if ai_response and len(ai_response.strip()) > 100:
                clean_desc = ai_response.strip()
                clean_desc = re.sub(r"^```(?:markdown|text)?\n?", "", clean_desc, flags=re.IGNORECASE)
                clean_desc = re.sub(r"\n?```$", "", clean_desc)
                return clean_desc.strip()
        except Exception as e:
            logger.warning(f"Failed to generate long description with AI: {e}")

        return fallback_desc

    def generate_tags(
        self,
        title: str,
        description: str,
        file_name: str,
    ) -> List[str]:
        """
        Generate 15 to 25 relevant, search-optimized YouTube tags.
        Falls back to comprehensive algorithmic tag generation from title/filename so tags are NEVER empty.
        """
        fallback_tags = self._generate_fallback_tags(title, file_name)
        prompt = f"""You are a YouTube SEO specialist.
Generate 15 to 25 highly relevant, high-traffic YouTube search tags for this video.

Video Title: {title}
Filename: {file_name}

Requirements:
- Target what people actually search for on YouTube (long-tail keywords, phrases, synonyms).
- Return ONLY valid JSON format:
{{"tags": ["tag 1", "tag 2", "tag 3", "tag 4", "tag 5", "tag 6", "tag 7", "tag 8", "tag 9", "tag 10", "tag 11", "tag 12", "tag 13", "tag 14", "tag 15"]}}
- Do not include explanations or markdown code blocks around the JSON.
"""
        try:
            ai_response = self._call_ai(prompt, temperature=0.5)
            if ai_response:
                # Strategy 1: JSON regex
                match = re.search(r"\{[\s\S]*\}", ai_response)
                if match:
                    try:
                        data = json.loads(match.group(0))
                        tags = data.get("tags", [])
                        if isinstance(tags, list) and len(tags) > 0:
                            clean_tags = self._clean_and_dedup_tags(tags)
                            if len(clean_tags) >= 5:
                                return clean_tags[:25]
                    except Exception:
                        pass

                # Strategy 2: Extract list array
                match_arr = re.search(r"\[([\s\S]*?)\]", ai_response)
                if match_arr:
                    try:
                        arr = json.loads(f"[{match_arr.group(1)}]")
                        clean_tags = self._clean_and_dedup_tags(arr)
                        if len(clean_tags) >= 5:
                            return clean_tags[:25]
                    except Exception:
                        pass

                # Strategy 3: Line-separated or comma-separated list
                lines = [line.strip().strip("-*•0123456789. \"'") for line in ai_response.splitlines()]
                lines = [l for l in lines if l and not l.startswith("{") and not l.startswith("}")]
                if len(lines) >= 5:
                    clean_tags = self._clean_and_dedup_tags(lines)
                    if len(clean_tags) >= 5:
                        return clean_tags[:25]
        except Exception as e:
            logger.warning(f"Failed to generate tags with AI or parse JSON: {e}")

        return fallback_tags

    def _generate_fallback_tags(self, title: str, file_name: str) -> List[str]:
        """
        Extract 15-25 robust search tags from title and filename using keyword decomposition,
        bigrams, trigrams, and relevant gaming/tech/tutorial keywords.
        Guarantees that a video NEVER uploads without tags.
        """
        combined = f"{title} {file_name}"
        raw_words = re.findall(r"[a-zA-Z0-9]+", combined)
        stop_words = {"a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "by", "from", "mp4", "mov", "avi", "mkv", "copy", "new", "final", "render"}
        meaningful_words = [w.lower() for w in raw_words if len(w) > 2 and w.lower() not in stop_words]

        candidates = []
        if title:
            candidates.append(title.lower()[:40])

        for i in range(len(meaningful_words) - 1):
            candidates.append(f"{meaningful_words[i]} {meaningful_words[i+1]}")

        for i in range(len(meaningful_words) - 2):
            candidates.append(f"{meaningful_words[i]} {meaningful_words[i+1]} {meaningful_words[i+2]}")

        candidates.extend(meaningful_words)

        lower_comb = combined.lower()
        if any(k in lower_comb for k in ["unity", "unreal", "game", "fps", "rpg", "character"]):
            candidates.extend(["game development", "unity tutorial", "character customization", "indie game dev", "unity 3d", "game dev", "unity assets", "gaming walkthrough"])
        if any(k in lower_comb for k in ["tutorial", "guide", "how to", "custom"]):
            candidates.extend(["how to", "tutorial", "beginner guide", "step by step", "tips and tricks"])
        if any(k in lower_comb for k in ["code", "script", "programming", "python", "dev"]):
            candidates.extend(["programming tutorial", "software development", "coding guide", "tech tips"])

        return self._clean_and_dedup_tags(candidates)[:25]

    def _clean_and_dedup_tags(self, tags: List[Any]) -> List[str]:
        cleaned = []
        seen = set()
        for t in tags:
            s = str(t).strip().strip('"\'#').lower()
            if s and len(s) >= 2 and len(s) <= 50 and s not in seen:
                seen.add(s)
                cleaned.append(s)
        return cleaned

    def generate_thumbnail(
        self,
        title: str,
        file_name: str,
        video_path: Optional[str | Path] = None,
        video_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a high-impact 16:9 YouTube video thumbnail directly aligned with the video's title.
        1. Attempts Gemini AI image generation (Imagen 3 / Gemini Flash Image).
        2. If AI image generation fails, encounters quota limits (429), or is unavailable,
           AUTOMATICALLY extracts and enhances a crisp 16:9 frame from the video using FFmpeg.
        3. If no video file is present, generates a branded 16:9 thumbnail graphic with FFmpeg.
        Guarantees that a thumbnail is ALWAYS generated and returned.
        """
        thumb_dir = Path(settings.THUMBNAIL_DIRECTORY)
        thumb_dir.mkdir(parents=True, exist_ok=True)
        safe_stem = re.sub(r"[^\w\-]", "_", Path(file_name).stem)[:40]
        identifier = video_id[:8] if video_id else str(int(time.time()))
        out_path = thumb_dir / f"thumb_{safe_stem}_{identifier}.jpg"

        api_key = self.gemini_api_key
        clean_title = self._clean_filename_to_title(file_name)
        subject = title if title and len(title) > 3 else clean_title

        # Layer 1: Attempt Gemini AI image generation if API key is present
        if api_key and not api_key.startswith("Option") and len(api_key) > 10:
            try:
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
                except Exception:
                    pass

                image_models = [
                    self.gemini_image_model or "imagen-3.0-generate-002",
                    "gemini-3.1-flash-image",
                    "gemini-2.5-flash-image",
                ]
                for model in image_models:
                    try:
                        # Attempt predict endpoint (Imagen)
                        url_predict = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}"
                        payload_predict = {
                            "instances": [{"prompt": visual_prompt}],
                            "parameters": {
                                "sampleCount": 1,
                                "aspectRatio": "16:9",
                                "outputMimeType": "image/jpeg",
                            },
                        }
                        with httpx.Client(timeout=45) as client:
                            res = client.post(url_predict, json=payload_predict)
                            if res.status_code == 200:
                                data = res.json()
                                predictions = data.get("predictions", [])
                                if predictions and "bytesBase64Encoded" in predictions[0]:
                                    b64_bytes = predictions[0]["bytesBase64Encoded"]
                                    img_data = base64.b64decode(b64_bytes)
                                    out_path.write_bytes(img_data)
                                    logger.info(f"AI Thumbnail generated with {model} and saved to: {out_path}")
                                    return str(out_path.resolve())

                        # Attempt generateContent endpoint (Gemini Flash Image)
                        url_gc = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                        payload_gc = {
                            "contents": [{"parts": [{"text": visual_prompt}]}],
                            "generationConfig": {"responseModalities": ["IMAGE"]},
                        }
                        with httpx.Client(timeout=45) as client:
                            res_gc = client.post(url_gc, json=payload_gc)
                            if res_gc.status_code == 200:
                                data_gc = res_gc.json()
                                candidates = data_gc.get("candidates", [])
                                if candidates:
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    for part in parts:
                                        if "inlineData" in part and "data" in part["inlineData"]:
                                            img_data = base64.b64decode(part["inlineData"]["data"])
                                            out_path.write_bytes(img_data)
                                            logger.info(f"AI Thumbnail generated via generateContent ({model}): {out_path}")
                                            return str(out_path.resolve())
                    except Exception as e:
                        logger.debug(f"Image model {model} attempt skipped: {e}")
            except Exception as e:
                logger.warning(f"AI image generation skipped or unavailable: {e}")

        # Layer 2: Automatic High-Quality Video Keyframe Extraction via FFmpeg
        if video_path and Path(video_path).exists():
            logger.info(f"Extracting high-resolution 16:9 thumbnail from video '{file_name}' using FFmpeg...")
            extracted_path = extract_and_enhance_thumbnail(video_path, out_path, title=subject)
            if extracted_path:
                logger.info(f"Automatic video thumbnail generated: {extracted_path}")
                return str(extracted_path)

        # Layer 3: Branded 16:9 Graphical Thumbnail fallback via FFmpeg
        logger.info(f"Generating branded 16:9 thumbnail graphic for '{subject}'...")
        graphic_path = create_graphic_thumbnail(out_path, title=subject)
        if graphic_path:
            return str(graphic_path)

        return None

    def _clean_filename_to_title(self, file_name: str) -> str:
        """Convert a filename like 'epic_gameplay_part_1.mp4' to 'Epic Gameplay Part 1'."""
        name = Path(file_name).stem
        name = re.sub(r"[_\-\.]+", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name.title()[:100] if name else "Untitled Video"
