# Module: Core Config (Pydantic BaseSettings)

## Overview

`core/config.py` manages all application configuration using Pydantic `BaseSettings`. Environment variables are loaded from `.env` via `python-dotenv`, validated through a `Settings` model, and exposed as both a singleton object and backward-compatible module-level aliases.

---

## File Path

`src/linkedin_action_center/core/config.py`

---

## Components & Explanation

- **`Settings`** — Pydantic `BaseSettings` subclass that validates and holds all configuration.
  - **Purpose**: Centralised, validated, type-safe configuration with fail-fast on invalid values.
  - **Inputs**: Environment variables from `.env` file or system environment.
  - **Outputs**: Validated `Settings` instance with typed attributes.
  - **Config**: `env_file=".env"`, `extra="ignore"` (unknown env vars are silently ignored).

- **Settings fields**:
  - `base_dir` — Project root (`Path`). Computed from `__file__`.
  - `data_dir` — `base_dir / "data"`. Created at import.
  - `snapshot_dir` — `data_dir / "snapshots"`. Created at import.
  - `tokens_file` — `base_dir / "tokens.json"`.
  - `database_file_path` — `data_dir / "linkedin_ads.db"`.
  - `linkedin_client_id` — LinkedIn app client ID (`Optional[str]`).
  - `linkedin_client_secret` — LinkedIn app secret (`Optional[str]`).
  - `linkedin_redirect_uri` — OAuth callback URL (default: `http://localhost:5000/callback`).
  - `oauth_state` — CSRF protection string (default: `supersecretstate`).
  - `freshness_ttl_minutes` — Minutes before a sync is considered stale (default: `240` = 4 hours).
  - `database_url` — Property that returns `sqlite:///{database_file_path}` for SQLAlchemy.

- **`settings`** — Module-level singleton of `Settings`.
- **Module-level aliases** — `BASE_DIR`, `DATA_DIR`, `SNAPSHOT_DIR`, `TOKENS_FILE`, `DATABASE_FILE`, `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_REDIRECT_URI`, `OAUTH_STATE` — backward-compatible aliases so existing `from config import DATABASE_FILE` imports continue to work.

---

## Relationships

- Imported by `auth/manager`, `storage/database`, `storage/repository`, `storage/snapshot`, `utils/logger`, `main.py`.
- `settings.database_url` is used by `storage/database.get_engine()` for SQLAlchemy.
- `settings.freshness_ttl_minutes` is used by `storage/repository.should_sync()`.
- Depends on `pydantic-settings` and `python-dotenv`.

---

## Example Code Snippets

```python
# Using the singleton (recommended for new code)
from linkedin_action_center.core.config import settings

print(f"DB URL: {settings.database_url}")
print(f"Freshness TTL: {settings.freshness_ttl_minutes} minutes")
print(f"Client ID set: {settings.linkedin_client_id is not None}")
```

```python
# Using backward-compatible aliases (legacy code)
from linkedin_action_center.core.config import (
    DATABASE_FILE,
    TOKENS_FILE,
    SNAPSHOT_DIR,
    LINKEDIN_CLIENT_ID,
)

print(f"DB path: {DATABASE_FILE}")
print(f"Tokens: {TOKENS_FILE}")
```

```bash
# .env file
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:5000/callback
OAUTH_STATE=my_random_state_string
FRESHNESS_TTL_MINUTES=240
```

---

## Edge Cases & Tips

- **Missing credentials**: `linkedin_client_id` and `linkedin_client_secret` default to `None`; auth will fail at runtime if not set. Pydantic does not enforce their presence because they are `Optional`.
- **BASE_DIR**: Computed from `__file__`; assumes standard package layout (`src/linkedin_action_center/core/config.py` -> 4 levels up). May break if config is moved.
- **OAuth state**: Use a random string in production for CSRF protection; default is not secure.
- **Redirect URI**: Must exactly match the URL configured in the LinkedIn Developer Portal.
- **Freshness TTL**: Set to 240 minutes (4 hours) by default. Override with `FRESHNESS_TTL_MINUTES` env var.
- **Extra fields**: `extra="ignore"` means unknown env vars are silently ignored, no errors.

---

## Architecture / Flow

```
Application startup
    |
    └── import linkedin_action_center.core.config
            ├── load_dotenv()
            ├── Settings() validates all env vars through Pydantic
            ├── settings = Settings()  (singleton)
            ├── data_dir.mkdir(exist_ok=True)
            ├── snapshot_dir.mkdir(exist_ok=True)
            └── Module-level aliases: BASE_DIR, DATABASE_FILE, etc.
```

---

## Advanced Notes

- `.env.example` in repo shows expected variables; `.env` is git-ignored.
- The `database_url` property dynamically constructs the SQLAlchemy connection string from `database_file_path`.
- `SettingsConfigDict(env_file=".env")` means Pydantic also tries to load `.env` independently of `load_dotenv()`. The explicit `load_dotenv()` call is kept for backward compatibility with code that reads `os.getenv()` directly.
- Paths are `pathlib.Path` objects; use `str(path)` when passing to `sqlite3.connect()`.
