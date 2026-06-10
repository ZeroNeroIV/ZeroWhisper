"""
AIProviderFactory — reads runtime config and creates the appropriate provider.

This eliminates the if/elif chain in the old openai_service._get_client() and
centralizes provider selection. New providers can be added by:
1. Creating a new class in providers.py
2. Adding a branch in this factory

The factory reads from ai_settings_service at call time, so provider changes
apply without restart.
"""
from __future__ import annotations

from app.core.config import settings
from app.core.ports.ai_provider import AIProvider, AIProviderFactory, TranscriptionProvider
from app.infrastructure.ai.providers import (
    OpenAIProvider,
    OpenAITranscriptionProvider,
    GroqTranscriptionProvider,
    LocalWhisperTranscriptionProvider,
)


def _s(key: str, fallback=None):
    """Read from runtime AI settings (JSON file), fall back to env config."""
    from app.infrastructure import ai_settings
    return ai_settings.get(key, fallback)


class ConfigDrivenAIProviderFactory(AIProviderFactory):
    """Creates providers based on ai_provider setting and runtime overrides."""

    def create_provider(self) -> AIProvider:
        provider = _s("ai_provider", settings.ai_provider)

        if provider == "gemini":
            return OpenAIProvider(
                api_key=_s("gemini_api_key", settings.gemini_api_key),
                base_url=settings.gemini_base_url,
                model=_s("gemini_model", settings.gemini_model),
            )
        if provider == "groq":
            return OpenAIProvider(
                api_key=_s("groq_api_key", settings.groq_api_key),
                base_url=settings.groq_base_url,
                model=_s("groq_model", settings.groq_model),
            )
        # Default: OpenAI
        return OpenAIProvider(
            api_key=_s("openai_api_key", settings.openai_api_key),
            base_url=_s("openai_base_url", settings.openai_base_url),
            model=_s("openai_model", settings.openai_model),
        )

    def create_transcription_provider(self) -> TranscriptionProvider:
        """Create with fallback chain: Groq → OpenAI → local faster-whisper."""
        groq_key = _s("groq_api_key", settings.groq_api_key)
        openai_key = _s("openai_api_key", settings.openai_api_key)

        if groq_key:
            return GroqTranscriptionProvider(
                api_key=groq_key,
                base_url=settings.groq_base_url,
                model=settings.groq_transcription_model,
            )
        if openai_key:
            return OpenAITranscriptionProvider(
                api_key=openai_key,
                base_url=_s("openai_base_url", settings.openai_base_url),
            )
        return LocalWhisperTranscriptionProvider(
            model_size=_s("local_whisper_model", settings.local_whisper_model),
            cache_dir=settings.whisper_cache_dir,
        )
