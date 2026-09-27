from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuthStatusResponse(BaseModel):
    is_authenticated: bool
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    token_expiry: Optional[datetime] = None
    scopes: Optional[str] = None
    has_drive_scope: bool = False
    has_youtube_scope: bool = False

    model_config = ConfigDict(from_attributes=True)


class AuthUrlResponse(BaseModel):
    authorization_url: str
