"""AI settings routes — GET/PUT for runtime LLM configuration."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.domain.user import User
from app.infrastructure import ai_settings

router = APIRouter(prefix="/api/ai-settings", tags=["ai-settings"])

PROVIDERS = Literal["openai", "gemini", "groq"]


class AiSettingsUpdate(BaseModel):
    ai_provider: PROVIDERS | None = None
    openai_api_key: str | None = None
    openai_model: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str | None = None
    groq_api_key: str | None = None
    groq_model: str | None = None
    local_whisper_model: str | None = None


@router.get("")
def get_ai_settings(_user: User = Depends(get_current_user)):
    masked = ai_settings.get_masked()
    return {**masked, **ai_settings.ai_status()}


@router.put("")
def update_ai_settings(
    body: AiSettingsUpdate,
    _user: User = Depends(get_current_user),
):
    ai_settings.update(body.model_dump(exclude_none=False))
    masked = ai_settings.get_masked()
    return {**masked, **ai_settings.ai_status()}
