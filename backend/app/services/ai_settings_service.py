"""
Runtime AI settings — persisted to data/ai_settings.json.

Values here override the pydantic config (env vars), so the user can
change provider/model/keys from the UI without editing .env.
"""
import json
from pathlib import Path

from app.config import settings

_runtime: dict | None = None  # None means not yet loaded


def _path() -> Path:
    p = Path(settings.ai_settings_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load() -> None:
    """Load from disk. Called once at startup."""
    global _runtime
    p = _path()
    _runtime = json.loads(p.read_text()) if p.exists() else {}


def _ensure_loaded() -> dict:
    global _runtime
    if _runtime is None:
        load()
    return _runtime  # type: ignore[return-value]


def get(key: str, fallback=None):
    """Return the runtime value for key, falling back to pydantic config or fallback."""
    val = _ensure_loaded().get(key)
    if val:
        return val
    return getattr(settings, key, None) or fallback


def get_all() -> dict:
    """Return all runtime settings merged with pydantic defaults."""
    cfg = _ensure_loaded()
    return {
        "ai_provider":          cfg.get("ai_provider") or settings.ai_provider,
        "openai_api_key":       cfg.get("openai_api_key") or settings.openai_api_key,
        "openai_model":         cfg.get("openai_model") or settings.whisper_model,
        "gemini_api_key":       cfg.get("gemini_api_key") or settings.gemini_api_key,
        "gemini_model":         cfg.get("gemini_model") or settings.gemini_model,
        "groq_api_key":         cfg.get("groq_api_key") or settings.groq_api_key,
        "local_whisper_model":  cfg.get("local_whisper_model") or settings.local_whisper_model,
    }


def _mask(key: str) -> str:
    if not key:
        return ""
    visible = key[:8]
    return visible + "•" * min(8, max(0, len(key) - 8))


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
        "local_whisper_model":  raw["local_whisper_model"],
    }


def update(patch: dict) -> None:
    """
    Persist a partial update. Keys with None values are skipped.
    Passing an empty string explicitly clears a key.
    Resets the cached AI clients so the next call picks up the new settings.
    """
    cfg = _ensure_loaded()
    for key, value in patch.items():
        if value is None:
            continue
        cfg[key] = value
    _path().write_text(json.dumps(cfg, indent=2))

    # Force client re-init in openai_service
    from app.services import openai_service
    openai_service.reset_clients()
