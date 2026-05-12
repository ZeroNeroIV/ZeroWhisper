from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = "change-me-in-production-use-32-random-chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    db_path: str = "data/zerowhisper.db"
    setup_state_path: str = "data/setup_state.json"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    whisper_model: str = "gpt-4o-mini"

    log_level: str = "INFO"
    auto_fetch_exchange_rate: bool = False
    default_exchange_rate: float = 0.709  # JOD per USD fallback

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
