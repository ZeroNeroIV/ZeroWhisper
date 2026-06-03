"""
Runtime AI settings manager — persists overrides to a JSON file.

Values here override pydantic-settings (env vars). This allows changing
AI provider, API keys, and models at runtime without restarting the server.
Single source of truth — no other module duplicates this state.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings

_runtime: dict | None = None
_state_path: Path = Path(settings.ai_settings_path)


def load() -> None:
    global _runtime
    if _state_path.exists():
        _runtime = json.loads(_state_path.read_text())
    else:
        _runtime = {}


def _ensure_loaded() -> dict:
    global _runtime
    if _runtime is None:
        load()
    return _runtime  # type: ignore[return-value]


def get(key: str, fallback=None):
    """Return runtime value, falling back to pydantic config or fallback."""
    val = _ensure_loaded().get(key)
    if val:
        return val
    return getattr(settings, key, None) or fallback


def get_all() -> dict:
    """Return runtime settings merged with pydantic defaults."""
    cfg = _ensure_loaded()
    return {
        "ai_provider":          cfg.get("ai_provider") or settings.ai_provider,
        "openai_api_key":       cfg.get("openai_api_key") or settings.openai_api_key,
        "openai_model":         cfg.get("openai_model") or settings.openai_model,
        "gemini_api_key":       cfg.get("gemini_api_key") or settings.gemini_api_key,
        "gemini_model":         cfg.get("gemini_model") or settings.gemini_model,
        "groq_api_key":         cfg.get("groq_api_key") or settings.groq_api_key,
        "groq_model":           cfg.get("groq_model") or "llama-3.3-70b-versatile",
        "local_whisper_model":  cfg.get("local_whisper_model") or settings.local_whisper_model,
    }


def _mask(key: str) -> str:
    """Mask all but last 4 characters of an API key for safe display."""
    if not key:
        return ""
    if len(key) <= 8:
        return key
    return key[:8] + "•" * min(8, max(0, len(key) - 8))


def get_masked() -> dict:
    """Return settings safe for API responses — API keys are masked."""
    raw = get_all()
    return {
        "ai_provider":          raw["ai_provider"],
        "openai_api_key":       _mask(raw["openai_api_key"]),
        "openai_model":         raw["openai_model"],
        "gemini_api_key":       _mask(raw["gemini_api_key"]),
        "gemini_model":         raw["gemini_model"],
        "groq_api_key":         _mask(raw["groq_api_key"]),
        "groq_model":           raw["groq_model"],
        "local_whisper_model":  raw["local_whisper_model"],
    }


def update(patch: dict) -> None:
    """Persist a partial update. Keys with None are skipped."""
    cfg = _ensure_loaded()
    for key, value in patch.items():
        if value is None:
            continue
        cfg[key] = value
    _state_path.write_text(json.dumps(cfg, indent=2))

    # Force client re-init so next call picks up new settings
    reset_clients()


# ── AI client lifecycle (cached OpenAI clients) ──────────────────────────────

_client: object | None = None
_transcription_client: object | None = None


def reset_clients() -> None:
    global _client, _transcription_client
    _client = None
    _transcription_client = None


def _get_model() -> str:
    provider = get("ai_provider", "openai")
    if provider == "gemini":
        return get("gemini_model", "gemini-2.5-flash")
    if provider == "groq":
        return get("groq_model", "llama-3.3-70b-versatile")
    return get("openai_model", "gpt-4o-mini")


def health_check() -> bool:
    provider = get("ai_provider", "openai")
    if provider == "gemini":
        return bool(get("gemini_api_key"))
    if provider == "groq":
        return bool(get("groq_api_key"))
    return bool(get("openai_api_key"))


def ai_status() -> dict:
    groq_key = get("groq_api_key")
    openai_key = get("openai_api_key")
    local_model = get("local_whisper_model", "small")
    transcription_backend = "groq" if groq_key else ("openai" if openai_key else f"local:{local_model}")
    return {
        "provider": get("ai_provider", "openai"),
        "model": _get_model(),
        "ai_ready": health_check(),
        "transcription_ready": True,
        "transcription_backend": transcription_backend,
    }
