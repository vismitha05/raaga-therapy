from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Raaga Therapy Adaptive Backend"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./raaga_therapy.db"
    eeg_window_seconds: int = 10
    eeg_poll_interval_seconds: float = 1.0
    websocket_channel_size: int = 300
    cors_allow_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
