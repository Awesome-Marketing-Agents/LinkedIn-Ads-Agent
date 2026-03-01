"""Application configuration backed by Pydantic Settings.

Reads from environment variables / ``.env`` file. Computes the
``SQLALCHEMY_DATABASE_URI`` from individual Postgres fields.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- Project paths -------------------------------------------------------
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    tokens_file: Path = Field(default=Path("tokens.json"))

    # -- PostgreSQL -----------------------------------------------------------
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "app"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "linkedin_ads"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # -- LinkedIn OAuth -------------------------------------------------------
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/callback"
    OAUTH_STATE: str = "supersecretstate"

    # -- CORS -----------------------------------------------------------------
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # -- Sync -----------------------------------------------------------------
    FRESHNESS_TTL_MINUTES: int = 240

    # -- Logging --------------------------------------------------------------
    LOG_LEVEL: str = "INFO"


settings = Settings()
