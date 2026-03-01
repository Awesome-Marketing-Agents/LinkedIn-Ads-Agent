# Module: Database (SQLite Schema, SQLAlchemy Engine & Session)

## Overview

`storage/database.py` defines the SQLite schema for the LinkedIn Ads Action Center and provides two interfaces for database access:

1. **Legacy**: `get_connection()` returns a raw `sqlite3.Connection` with WAL mode and schema applied.
2. **Modern**: `get_engine()` returns a cached SQLAlchemy `Engine`, and `get_session()` yields a SQLModel `Session` for ORM-based access.

All seven tables are created automatically when the schema is applied.

---

## File Path

`src/linkedin_action_center/storage/database.py`

---

## Components & Explanation

### Schema (`_SCHEMA`)

SQL script defining seven tables:

| Table | Primary Key | Purpose |
|-------|-------------|---------|
| `ad_accounts` | `id` (INTEGER) | Ad account metadata |
| `campaigns` | `id` (INTEGER) | Campaign settings, budgets, targeting flags |
| `creatives` | `id` (TEXT) | Creative metadata, serving status |
| `campaign_daily_metrics` | `(campaign_id, date)` | Daily time-series metrics per campaign |
| `creative_daily_metrics` | `(creative_id, date)` | Daily time-series metrics per creative |
| `audience_demographics` | `(account_id, pivot_type, segment, date_start)` | Aggregated demographic segments |
| `sync_log` | `id` (AUTOINCREMENT) | Sync run tracking for freshness gate |

### Legacy Interface

- **`init_database(db_path=None)`** — Create schema and return database path.
- **`get_connection(db_path=None)`** — Return `sqlite3.Connection` with WAL mode and schema applied. Used by freshness gate functions in `repository.py`.

### SQLAlchemy Interface

- **`get_engine(db_url=None)`** — Return a cached SQLAlchemy `Engine` singleton. Registers a `connect` event listener to set WAL mode on every new connection.
- **`get_session(db_url=None)`** — Context manager that yields a `SQLModel.Session` bound to the engine. Used by `persist_snapshot()` for ORM-based upserts.

---

## Relationships

- Used by `storage/repository.py` for all persistence and queries.
- `get_engine()` reads `settings.database_url` from `core.config` when `db_url` is not provided.
- `get_connection()` reads `DATABASE_FILE` from `core.config`.
- SQLModel table definitions live in `models/db_models.py` (see [17-models-db.md](17-models-db.md)).
- Alembic migrations also target this database (see [18-alembic-migrations.md](18-alembic-migrations.md)).

---

## Example Code Snippets

```python
# Legacy: raw sqlite3 connection
from linkedin_action_center.storage.database import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM campaigns")
print(cur.fetchone()[0])
conn.close()
```

```python
# Modern: SQLAlchemy session (recommended for new code)
from linkedin_action_center.storage.database import get_session

with get_session() as session:
    from linkedin_action_center.models.db_models import Campaign
    campaigns = session.exec(select(Campaign)).all()
    print(f"Found {len(campaigns)} campaigns")
```

```python
# Custom path (e.g., tests)
from linkedin_action_center.storage.database import get_engine

engine = get_engine("sqlite:///tmp/test.db")
```

---

## Edge Cases & Tips

- **Schema application**: `executescript(_SCHEMA)` runs on every `get_connection()`; `CREATE TABLE IF NOT EXISTS` is idempotent.
- **WAL mode**: Set via `PRAGMA journal_mode=WAL` on both the legacy and SQLAlchemy interfaces.
- **Engine caching**: `get_engine()` caches the engine globally. Pass a `db_url` to create a new engine (used in tests).
- **Path**: Default is `data/linkedin_ads.db`; `data/` is created by `core/config`.
- **Foreign keys**: Schema defines `FOREIGN KEY` but SQLite does not enforce them by default; enable with `PRAGMA foreign_keys=ON` if needed.
- **Composite primary keys**: Metrics and demographics tables use composite keys to prevent duplicates.

---

## Architecture / Flow

```
Repository / Tests
    |
    ├── get_connection(db_path)          [Legacy path]
    │       ├── sqlite3.connect(path)
    │       ├── PRAGMA journal_mode=WAL
    │       ├── conn.executescript(_SCHEMA)
    │       └── return conn
    |
    └── get_session(db_url)              [Modern path]
            ├── get_engine(db_url)
            │       ├── create_engine(url)
            │       └── @event: PRAGMA journal_mode=WAL
            └── Session(engine) -> yield session
```

---

## Advanced Notes

- Primary keys: `ad_accounts.id`, `campaigns.id`, `creatives.id` (TEXT for creatives); composite keys for metrics and demographics tables.
- `fetched_at` columns store ISO timestamps for audit trail.
- Derived metrics (ctr, cpc) are stored in metrics tables, not computed on read.
- `sync_log` table tracks every sync run: start time, finish time, status, counts, and errors. Used by the freshness gate (`should_sync()`) to avoid redundant API calls.
- The dual interface (legacy + SQLAlchemy) exists for backward compatibility. New code should use `get_session()`.
