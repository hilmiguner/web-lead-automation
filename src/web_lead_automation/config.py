"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the application.

    Secrets are read from environment variables or a local ``.env`` file.
    The ``.env`` file is intentionally ignored by git.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    google_places_api_key: str | None = Field(default=None, repr=False)
    google_places_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    google_places_page_size: int = Field(default=20, ge=1, le=20)
    lead_db_path: Path = Path("data/leads.sqlite3")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached application settings instance."""

    return Settings()
