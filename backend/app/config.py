from pydantic import model_validator
from pydantic_settings import BaseSettings

_INSECURE_DEFAULT = "change-me-in-production-use-32-random-chars"


class Settings(BaseSettings):
    jwt_secret: str = _INSECURE_DEFAULT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    db_path: str = "data/zerowhisper.db"
    setup_state_path: str = "data/setup_state.json"
    ai_settings_path: str = "data/ai_settings.json"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    whisper_model: str = "gpt-4o-mini"

    groq_api_key: str = ""

    # Local Whisper (faster-whisper). Model downloaded on first use.
    # Options: tiny, base, small, medium, large-v3
    local_whisper_model: str = "small"
    whisper_cache_dir: str = "/app/models"

    ai_provider: str = "openai"  # "openai" or "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    log_level: str = "INFO"
    auto_fetch_exchange_rate: bool = False
    default_exchange_rate: float = 0.709  # JOD per USD fallback

    @model_validator(mode="after")
    def _reject_insecure_default(self) -> "Settings":
        if self.jwt_secret == _INSECURE_DEFAULT:
            raise ValueError(
                "jwt_secret must be set to a secure random value in your .env file. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
