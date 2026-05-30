from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "P店データリサーチ"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/pdata"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    # 操作系API（店舗登録・データソース追加・バッチ実行）の保護用APIキー。
    # 本番では必ず環境変数で上書きすること。
    ADMIN_API_KEY: str = "change-me-admin-key"

    # Scraping
    SCRAPE_REQUEST_INTERVAL: float = 2.0  # seconds between requests
    SCRAPE_TIMEOUT: int = 30
    SCRAPE_MAX_CONCURRENCY: int = 3
    SCRAPE_MAX_RETRIES: int = 3
    SCRAPE_RETRY_INTERVAL: int = 60

    # Notifications
    CHATWORK_API_TOKEN: str = ""
    CHATWORK_ROOM_ID: str = ""
    SLACK_WEBHOOK_URL: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
