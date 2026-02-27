# Module: Core Config (Environment & Paths)

## Overview

`core/config.py` loads environment variables and defines paths for tokens, database, and snapshots. It is the single source of configuration for the application.

---

## File Path

`src/linkedin_action_center/core/config.py`

---

## Components & Explanation

- **`load_dotenv()`** — Loads `.env` from project root (called at import).
- **`BASE_DIR`** — Project root (`parent.parent.parent.parent` of config file = project root).
- **`DATA_DIR`** — `BASE_DIR / "data"`.
- **`SNAPSHOT_DIR`** — `DATA_DIR / "snapshots"`.
- **`TOKENS_FILE`** — `BASE_DIR / "tokens.json"`.
- **`DATABASE_FILE`** — `DATA_DIR / "linkedin_ads.db"`.
- **`LINKEDIN_CLIENT_ID`** — From `LINKEDIN_CLIENT_ID` env var.
- **`LINKEDIN_CLIENT_SECRET`** — From `LINKEDIN_CLIENT_SECRET` env var.
- **`LINKEDIN_REDIRECT_URI`** — From `LINKEDIN_REDIRECT_URI` env var (default: `http://localhost:5000/callback`).
- **`OAUTH_STATE`** — From `OAUTH_STATE` env var (default: `supersecretstate`).
- **Directory creation** — `DATA_DIR.mkdir(exist_ok=True)` and `SNAPSHOT_DIR.mkdir(exist_ok=True)` run at import.

---

## Relationships

- Imported by `auth/manager`, `storage/database`, `storage/snapshot`, `utils/logger`, `main.py`.
- Depends on `python-dotenv` for `.env` loading.
- No other config files; all settings come from env or defaults.

---

## Example Code Snippets

```python
from linkedin_action_center.core.config import (
    DATABASE_FILE,
    TOKENS_FILE,
    SNAPSHOT_DIR,
    LINKEDIN_CLIENT_ID,
    OAUTH_STATE,
)

print(f"DB path: {DATABASE_FILE}")
print(f"Tokens: {TOKENS_FILE}")
print(f"OAuth state: {OAUTH_STATE}")
```

```bash
# .env file
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:5000/callback
OAUTH_STATE=my_random_state_string
```

---

## Edge Cases & Tips

- **Missing .env**: Variables default to `None` or strings; auth will fail if credentials are missing.
- **BASE_DIR**: Computed from `__file__`; assumes standard package layout. May break if config is moved.
- **OAuth state**: Use a random string in production for CSRF protection; default is not secure.
- **Redirect URI**: Must exactly match the URL configured in the LinkedIn Developer Portal.

---

## Architecture / Flow

```
Application startup
    │
    └── import linkedin_action_center.core.config
            ├── load_dotenv()
            ├── BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
            ├── DATA_DIR, SNAPSHOT_DIR, TOKENS_FILE, DATABASE_FILE = ...
            ├── LINKEDIN_* = os.getenv(...)
            └── DATA_DIR.mkdir(exist_ok=True), SNAPSHOT_DIR.mkdir(exist_ok=True)
```

---

## Advanced Notes

- `.env.example` in repo shows expected variables; `.env` is git-ignored.
- No validation of config values at import; failures surface when auth or DB is used.
- Paths are `pathlib.Path` objects; use `str(path)` when passing to `sqlite3.connect()`.
