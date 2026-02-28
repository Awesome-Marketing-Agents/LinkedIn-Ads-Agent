"""Application configuration backed by Pydantic BaseSettings.

Environment variables are loaded from ``.env`` (via *python-dotenv*) and
validated through a ``Settings`` model.  Module-level aliases are kept for
backward compatibility so that existing ``from config import DATABASE_FILE``
imports continue to work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

# ---------------------------------------------------------------------------
# Resolve the project root once (four levels up from this file).
# ---------------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Centralised, validated application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- Paths (not typically set via env vars) ----------------------------
    base_dir: Path = _BASE_DIR
    data_dir: Path = _BASE_DIR / "data"
    snapshot_dir: Path = _BASE_DIR / "data" / "snapshots"
    tokens_file: Path = _BASE_DIR / "tokens.json"
    database_file_path: Path = _BASE_DIR / "data" / "linkedin_ads.db"

    # -- LinkedIn OAuth credentials ----------------------------------------
    linkedin_client_id: Optional[str] = Field(default=None)
    linkedin_client_secret: Optional[str] = Field(default=None)
    linkedin_redirect_uri: str = Field(
        default="http://localhost:5000/callback",
    )

    # -- Security ----------------------------------------------------------
    oauth_state: str = Field(default="supersecretstate")

    # -- Sync tuning -------------------------------------------------------
    freshness_ttl_minutes: int = Field(
        default=240,
        description="Minutes before a sync is considered stale and re-run.",
    )

    # -- Database URL for SQLAlchemy / Alembic ----------------------------
    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_file_path}"


# Singleton ----------------------------------------------------------------
settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(exist_ok=True)
settings.snapshot_dir.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Backward-compatible module-level aliases
# ---------------------------------------------------------------------------
BASE_DIR = settings.base_dir
DATA_DIR = settings.data_dir
SNAPSHOT_DIR = settings.snapshot_dir
TOKENS_FILE = settings.tokens_file
DATABASE_FILE = settings.database_file_path

LINKEDIN_CLIENT_ID = settings.linkedin_client_id
LINKEDIN_CLIENT_SECRET = settings.linkedin_client_secret
LINKEDIN_REDIRECT_URI = settings.linkedin_redirect_uri

OAUTH_STATE = settings.oauth_state
