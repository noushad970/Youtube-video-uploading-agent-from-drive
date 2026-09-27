from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AgentSettingsSchema(BaseModel):
    id: Optional[int] = None
    enabled: bool = False
    interval_minutes: int = Field(default=360, ge=5, le=10080)
    privacy_status: str = Field(default="private")
    category_id: str = Field(default="20")
    generate_title: bool = True
    generate_description: bool = True
    generate_tags: bool = True
    ollama_model: str = "qwen3:8b"
    max_retries: int = Field(default=3, ge=1, le=10)
    delete_after_upload: bool = True
    fallback_if_ai_unavailable: bool = True
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AgentSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    interval_minutes: Optional[int] = Field(default=None, ge=5, le=10080)
    privacy_status: Optional[str] = None
    category_id: Optional[str] = None
    generate_title: Optional[bool] = None
    generate_description: Optional[bool] = None
    generate_tags: Optional[bool] = None
    ollama_model: Optional[str] = None
    max_retries: Optional[int] = Field(default=None, ge=1, le=10)
    delete_after_upload: Optional[bool] = None
    fallback_if_ai_unavailable: Optional[bool] = None
