"""
AI settings router — GET/PUT for runtime LLM configuration.
"""
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.models.user import User
from app.services import ai_settings_service

router = APIRouter()

PROVIDERS = Literal["openai", "gemini", "groq"]


class AiSettingsUpdate(BaseModel):
    ai_provider: PROVIDERS | None = None
    openai_api_key: str | None = None
    openai_model: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str | None = None
    groq_api_key: str | None = None
    local_whisper_model: str | None = None


@router.get("")
def get_ai_settings(_user: User = Depends(get_current_user)):
    """Return current AI settings. API keys are masked."""
    masked = ai_settings_service.get_masked()
    from app.services.openai_service import ai_status
    status = ai_status()
    return {**masked, **status}


@router.put("")
def update_ai_settings(
    body: AiSettingsUpdate,
    _user: User = Depends(get_current_user),
):
    """
    Update AI settings. Only non-None fields are applied.
    API key fields: pass new key to update, pass "" to clear, omit/null to keep current.
    """
    ai_settings_service.update(body.model_dump(exclude_none=False))
    masked = ai_settings_service.get_masked()
    from app.services.openai_service import ai_status
    status = ai_status()
    return {**masked, **status}
