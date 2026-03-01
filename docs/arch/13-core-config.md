# Module: Application Configuration

## Overview

`config.py` defines the application settings using Pydantic `BaseSettings`. All configuration is loaded from environment variables or a `.env` file, with typed defaults. The PostgreSQL connection URI is computed from individual fields.

---

## File Path

`backend/app/core/config.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `pydantic.Field` | Default values |
| `pydantic.computed_field` | Derived `SQLALCHEMY_DATABASE_URI` |
| `pydantic_settings.BaseSettings` | Env var loading |

---

## Components

### `Settings(BaseSettings)`

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
```

**`extra="ignore"`**: Unknown env vars are silently ignored, preventing startup failures.

**`.env` location**: Resolved to project root (4 levels up from `core/config.py`).

### Settings Fields

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `base_dir` | `Path` | `backend/` | Project base directory |
| `tokens_file` | `Path` | `tokens.json` | OAuth token persistence |
| `POSTGRES_HOST` | `str` | `"localhost"` | Database host |
| `POSTGRES_PORT` | `int` | `5432` | Database port |
| `POSTGRES_USER` | `str` | `"app"` | Database user |
| `POSTGRES_PASSWORD` | `str` | `"changeme"` | Database password |
| `POSTGRES_DB` | `str` | `"linkedin_ads"` | Database name |
| `LINKEDIN_CLIENT_ID` | `Optional[str]` | `None` | OAuth client ID |
| `LINKEDIN_CLIENT_SECRET` | `Optional[str]` | `None` | OAuth client secret |
| `LINKEDIN_REDIRECT_URI` | `str` | `http://localhost:8000/api/v1/auth/callback` | OAuth redirect |
| `OAUTH_STATE` | `str` | `"supersecretstate"` | CSRF state parameter |
| `BACKEND_CORS_ORIGINS` | `list[str]` | `["http://localhost:5173", "http://localhost:3000"]` | Allowed origins |
| `FRESHNESS_TTL_MINUTES` | `int` | `240` | Min minutes between syncs |
| `LOG_LEVEL` | `str` | `"INFO"` | Logging verbosity |

### `SQLALCHEMY_DATABASE_URI` (computed property)

```python
@computed_field
@property
def SQLALCHEMY_DATABASE_URI(self) -> str:
    return (
        f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
        f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    )
```

**Purpose**: Construct the PostgreSQL connection string from individual fields. Uses `psycopg` (v3) driver.

### `settings` Singleton

```python
settings = Settings()
```

Module-level instance, imported throughout the app.

---

## Code Snippet

```python
from app.core.config import settings

print(settings.SQLALCHEMY_DATABASE_URI)
# postgresql+psycopg://app:changeme@localhost:5432/linkedin_ads

print(settings.FRESHNESS_TTL_MINUTES)
# 240
```

---

## Relationships

- **Used by**: `core/db.py` (database URI), `core/security.py` (OAuth credentials), `main.py` (CORS, log level), `crud/sync_log.py` (freshness TTL)
