from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.google_auth_service import GoogleAuthService
from app.schemas.auth import AuthStatusResponse, AuthUrlResponse
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/google", response_model=AuthUrlResponse)
def get_google_auth_url(
    redirect: bool = Query(default=False, description="If true, directly redirects browser"),
    db: Session = Depends(get_db),
):
    """Generate Google OAuth 2.0 authorization URL."""
    try:
        service = GoogleAuthService(db)
        url = service.get_authorization_url()
        if redirect:
            return RedirectResponse(url=url)
        return AuthUrlResponse(authorization_url=url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/google/callback")
def google_auth_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Handle Google OAuth 2.0 authorization callback."""
    if error:
        return RedirectResponse(url=f"http://localhost:5173/google-account?error={error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    try:
        service = GoogleAuthService(db)
        service.handle_auth_callback(code)
        # Redirect to frontend dashboard with success query param
        return RedirectResponse(url="http://localhost:5173/google-account?auth=success")
    except Exception as e:
        return RedirectResponse(url=f"http://localhost:5173/google-account?error={str(e)}")


@router.get("/status", response_model=AuthStatusResponse)
def get_auth_status(db: Session = Depends(get_db)):
    """Check current Google connection status and available scopes."""
    service = GoogleAuthService(db)
    status = service.get_auth_status()
    return AuthStatusResponse(**status)


@router.post("/disconnect")
def disconnect_google(db: Session = Depends(get_db)):
    """Revoke Google token and disconnect account."""
    service = GoogleAuthService(db)
    service.disconnect()
    return {"success": True, "message": "Google account disconnected successfully."}
