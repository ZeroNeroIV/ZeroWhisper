"""
Application configuration — single source of truth for ALL settings.

Every tunable value in the system lives here. No file in the codebase
may hardcode a timeout, URL, limit, or algorithm parameter that could
reasonably be env-configured. If a value differs between environments
(dev/staging/prod), it must be an env var with a documented default.

Validation rules are enforced at construction time, not at use time.
"""
from __future__ import annotations

from pathlib import Path
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Auth ──────────────────────────────────────────────────────────────────────
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── Paths ─────────────────────────────────────────────────────────────────────
    db_dir: str = "data"
    setup_state_path: str = "data/setup_state.json"
    ai_settings_path: str = "data/ai_settings.json"

    # ── SQLCipher ─────────────────────────────────────────────────────────────────
    cipher_algorithm: str = "aes-256-cfb"
    cipher_kdf_iter: int = 64000
    pbkdf2_iterations: int = 260_000
    pbkdf2_hash: str = "sha256"
    pbkdf2_salt_bytes: int = 32

    # ── AI Provider (OpenAI) ──────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # ── AI Provider (Groq) ────────────────────────────────────────────────────────
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # ── AI Provider (Gemini) ──────────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # ── AI Runtime (overridable via ai_settings.json) ─────────────────────────────
    ai_provider: str = "openai"  # "openai" | "gemini" | "groq"

    # ── Local Whisper ─────────────────────────────────────────────────────────────
    local_whisper_model: str = "small"
    whisper_cache_dir: str = "/app/models"

    # ── Exchange Rates ────────────────────────────────────────────────────────────
    auto_fetch_exchange_rate: bool = False
    default_exchange_rate: float = 0.709  # JOD per USD fallback

    # ── Bank Sync ─────────────────────────────────────────────────────────────────
    bank_sync_interval_seconds: int = 3600

    # ── Whisper Proposals ─────────────────────────────────────────────────────────
    whisper_proposal_ttl_minutes: int = 15

    # ── API Keys ──────────────────────────────────────────────────────────────────
    api_key_prefix: str = "zwp_"
    api_key_bytes: int = 32

    # ── Logging ───────────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    @field_validator("jwt_secret")
    @classmethod
    def _jwt_secret_must_be_set(cls, v: str) -> str:
        if not v or v == "change-me-in-production-use-32-random-chars":
            raise ValueError(
                "jwt_secret must be set to a secure random value in your .env file. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if len(v) < 32:
            raise ValueError("jwt_secret must be at least 32 characters")
        return v

    @field_validator("ai_provider")
    @classmethod
    def _validate_provider(cls, v: str) -> str:
        allowed = {"openai", "gemini", "groq"}
        if v not in allowed:
            raise ValueError(f"ai_provider must be one of {allowed}, got {v!r}")
        return v

    @model_validator(mode="after")
    def _validate_ai_key_for_provider(self) -> Settings:
        key_map = {
            "openai": self.openai_api_key,
            "gemini": self.gemini_api_key,
            "groq": self.groq_api_key,
        }
        if self.ai_provider in key_map and not key_map[self.ai_provider]:
            import warnings
            warnings.warn(
                f"ai_provider is '{self.ai_provider}' but no API key is configured. "
                f"Set {self.ai_provider}_api_key or switch ai_provider."
            )
        return self

    @property
    def db_path(self) -> str:
        return str(Path(self.db_dir) / "zerowhisper.db")

    def vault_db_path(self, vault_id: str) -> str:
        return str(Path(self.db_dir) / f"vault-{vault_id}.db")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
