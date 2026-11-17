import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.repository import Repository
from app.schemas.settings import (
    AgentSettingsSchema,
    AgentSettingsUpdate,
    GeminiKeyVerifyRequest,
    GeminiKeyVerifyResponse,
)
from app.services.scheduler_service import SchedulerService

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=AgentSettingsSchema)
def get_settings(db: Session = Depends(get_db)):
    """Retrieve current agent configuration settings."""
    repo = Repository(db)
    return repo.get_settings()


@router.put("", response_model=AgentSettingsSchema)
def update_settings(
    update_data: AgentSettingsUpdate,
    db: Session = Depends(get_db),
):
    """Update agent configuration settings."""
    repo = Repository(db)
    data = update_data.model_dump(exclude_unset=True)

    if data.get("enabled") is True:
        curr = repo.get_settings()
        target_provider = data.get("ai_provider") or curr.ai_provider or "gemini"
        target_key = data.get("gemini_api_key") if "gemini_api_key" in data else curr.gemini_api_key
        if target_provider == "gemini" and (not target_key or len(str(target_key).strip()) <= 10):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="Warning: No Gemini API Key provided! You must give a valid Gemini API key first before activating automated uploads.",
            )

    updated = repo.update_settings(**data)

    # If enabled or interval changed, update scheduler
    if "interval_minutes" in data or "enabled" in data:
        if updated.enabled:
            SchedulerService.reschedule(updated.interval_minutes)
        else:
            SchedulerService.pause_job()

    return updated


@router.post("/verify-gemini-key", response_model=GeminiKeyVerifyResponse)
def verify_gemini_key(
    req: GeminiKeyVerifyRequest,
    db: Session = Depends(get_db),
):
    """Test and verify that a Google Gemini API Key is valid with Gemini 3.5."""
    repo = Repository(db)
    current_settings = repo.get_settings()
    key_to_test = (req.api_key or "").strip()
    if not key_to_test:
        key_to_test = (current_settings.gemini_api_key or "").strip()

    if not key_to_test:
        return GeminiKeyVerifyResponse(
            valid=False,
            message="No API key provided. Please paste your Gemini API key from Google AI Studio.",
            model=req.model or "gemini-3.5-flash-lite",
        )

    model = req.model or current_settings.gemini_model or "gemini-3.5-flash-lite"
    if any(old in model.lower() for old in ["2.5", "1.5", "1.0", "gemini-pro"]):
        model = "gemini-3.5-flash-lite"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key_to_test}"
    payload = {
        "contents": [{"parts": [{"text": "Reply with 'OK'."}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 5},
    }

    try:
        with httpx.Client(timeout=15) as client:
            res = client.post(url, json=payload)
            if res.status_code == 200:
                return GeminiKeyVerifyResponse(
                    valid=True,
                    message=f"Success! Gemini API Key is active & verified with '{model}'.",
                    model=model,
                )
            else:
                try:
                    data = res.json()
                    err = data.get("error", {}).get("message", res.text)
                except Exception:
                    err = res.text
                return GeminiKeyVerifyResponse(
                    valid=False,
                    message=f"Gemini API returned error ({res.status_code}): {err}",
                    model=model,
                )
    except httpx.TimeoutException:
        return GeminiKeyVerifyResponse(
            valid=False,
            message="Connection to Google AI Studio timed out. Please check your internet connection.",
            model=model,
        )
    except Exception as e:
        return GeminiKeyVerifyResponse(
            valid=False,
            message=f"Verification failed: {str(e)}",
            model=model,
        )

