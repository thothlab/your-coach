from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str
    telegram_bot_username: str = "trainbeat_bot"
    telegram_webapp_url: str = "https://localhost:5173"
    telegram_webhook_secret: str = "dev-only-secret"
    public_base_url: str = "http://localhost:8000"
    database_url: str
    app_env: str = "dev"
    mini_app_dist: str = "mini-app/dist"
    scheduler_interval_minutes: int = 15


settings = Settings()
