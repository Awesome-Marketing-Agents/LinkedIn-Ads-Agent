# Module: Database (SQLite Schema & Connection)

## Overview

`storage/database.py` defines the SQLite schema for the LinkedIn Ads Action Center and provides `get_connection()` so other modules can obtain a ready-to-use connection. All six tables are created automatically when the schema is applied.

---

## File Path

`src/linkedin_action_center/storage/database.py`

---

## Components & Explanation

- **`_SCHEMA`** — SQL script defining six tables:
  - `ad_accounts` — Ad account metadata (id, name, status, currency, type, is_test, fetched_at)
  - `campaigns` — Campaign settings (id, account_id, name, status, type, budgets, bid_strategy, etc.)
  - `creatives` — Creative metadata (id, campaign_id, account_id, intended_status, is_serving, etc.)
  - `campaign_daily_metrics` — Daily time-series metrics per campaign
  - `creative_daily_metrics` — Daily time-series metrics per creative
  - `audience_demographics` — Aggregated demographic segments (account_id, pivot_type, segment, impressions, etc.)

- **`init_database(db_path=None)`** — Create schema and return database path. Used for initialization.
- **`get_connection(db_path=None)`** — Return `sqlite3.Connection` with WAL mode and schema applied. Main entry point for all DB access.

---

## Relationships

- Used by `storage/repository.py` for all persistence and queries.
- Reads `DATABASE_FILE` from `core.config` when `db_path` is not provided.
- No other modules import this directly; they go through `repository`.

---

## Example Code Snippets

```python
from linkedin_action_center.storage.database import get_connection, init_database

# Initialize (creates file and schema)
path = init_database()
print(f"Database at: {path}")

# Get connection for queries
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM campaigns")
print(cur.fetchone()[0])
conn.close()
```

```python
# Use with custom path (e.g., tests)
from pathlib import Path
conn = get_connection(Path("/tmp/test.db"))
```

---

## Edge Cases & Tips

- **Schema application**: `executescript(_SCHEMA)` runs on every `get_connection()`; `CREATE TABLE IF NOT EXISTS` is idempotent.
- **WAL mode**: `PRAGMA journal_mode=WAL` improves concurrent read performance.
- **Path**: Default is `data/linkedin_ads.db`; `data/` is created by `core/config`.
- **Foreign keys**: Schema defines `FOREIGN KEY` but SQLite does not enforce them by default; enable with `PRAGMA foreign_keys=ON` if needed.

---

## Architecture / Flow

```
Repository / Tests
    │
    └── get_connection(db_path)
            ├── sqlite3.connect(path)
            ├── PRAGMA journal_mode=WAL
            ├── conn.executescript(_SCHEMA)
            └── return conn
```

---

## Advanced Notes

- Primary keys: `ad_accounts.id`, `campaigns.id`, `creatives.id` (TEXT for creatives); composite keys for metrics tables.
- `fetched_at` columns store ISO timestamps for audit.
- Derived metrics (ctr, cpc) are stored in metrics tables, not computed on read.

---

## Node.js Equivalent

**Files**: `node-app/src/storage/database.ts` + `node-app/src/storage/schema.ts`

The Node.js port splits `storage/database.py` into two files: one for connection management and raw schema init, and one for type-safe table definitions via Drizzle ORM.

### Key Mappings

| Python | Node.js |
|--------|---------|
| `storage/database.py` | `node-app/src/storage/database.ts` (connection + raw SQL schema) |
| -- | `node-app/src/storage/schema.ts` (Drizzle ORM table definitions) |
| `sqlite3` (stdlib) | `better-sqlite3` (synchronous C binding) |
| `_SCHEMA` SQL string | Raw `CREATE TABLE IF NOT EXISTS` statements in `database.ts` |

### Preserved Patterns

- **Same WAL mode** (`PRAGMA journal_mode=WAL`) for concurrent read performance.
- **Same 6 tables** with identical columns: `ad_accounts`, `campaigns`, `creatives`, `campaign_daily_metrics`, `creative_daily_metrics`, `audience_demographics`.
- **Same idempotent schema application** using `CREATE TABLE IF NOT EXISTS` on every connection.
- **`get_connection()` equivalent** returns a `better-sqlite3` Database instance.

### Key Additions

- **`schema.ts`** defines all six tables using Drizzle ORM, providing **TypeScript types for all table columns**. This gives compile-time type safety when reading from or writing to the database.
- **`better-sqlite3`** is a synchronous C binding, which matches the behavior of Python's built-in `sqlite3` module -- no async overhead for local database operations.
- The raw SQL schema in `database.ts` is used for `CREATE TABLE IF NOT EXISTS` initialization, while the Drizzle schema in `schema.ts` is used for type-safe query building in the repository layer.
