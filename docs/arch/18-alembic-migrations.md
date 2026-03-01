# Module: Database Migrations (Alembic)

## Overview

The `alembic/` directory manages database schema migrations for the LinkedIn Ads Action Center. Alembic tracks schema changes over time and applies them incrementally, ensuring the database stays in sync with the SQLModel definitions in `models/db_models.py`.

---

## File Paths

- `alembic.ini` — Alembic configuration (connection string, script location).
- `alembic/env.py` — Migration environment setup (imports SQLModel metadata).
- `alembic/script.py.mako` — Template for new migration files.
- `alembic/versions/0001_initial_schema.py` — Initial migration matching the raw SQL schema.

---

## Components & Explanation

### Configuration (`alembic.ini`)

```ini
sqlalchemy.url = sqlite:///data/linkedin_ads.db
script_location = alembic
prepend_sys_path = src
```

- **`sqlalchemy.url`**: Points to the SQLite database.
- **`script_location`**: Directory containing migration scripts.
- **`prepend_sys_path`**: Adds `src/` to Python path so `linkedin_action_center` can be imported.

### Environment (`alembic/env.py`)

- Imports `SQLModel` and all table models from `models/db_models`.
- Sets `target_metadata = SQLModel.metadata` — this tells Alembic what the schema **should** look like.
- Configures both offline (SQL generation) and online (direct DB connection) migration modes.

### Initial Migration (`0001_initial_schema.py`)

Creates all 7 tables matching the raw SQL schema in `storage/database.py`:

| Table | Key Columns |
|-------|-------------|
| `ad_accounts` | `id` (PK), `name`, `status`, `currency`, `type`, `is_test`, `fetched_at` |
| `campaigns` | `id` (PK), `account_id` (FK), budgets, targeting flags, `fetched_at` |
| `creatives` | `id` TEXT (PK), `campaign_id` (FK), `account_id` (FK), `is_serving`, `fetched_at` |
| `campaign_daily_metrics` | `(campaign_id, date)` composite PK, 10 metric columns |
| `creative_daily_metrics` | `(creative_id, date)` composite PK, 10 metric columns |
| `audience_demographics` | `(account_id, pivot_type, segment, date_start)` composite PK |
| `sync_log` | `id` AUTOINCREMENT, `account_id`, `started_at`, `status`, sync stats |

The `downgrade()` function drops all tables in reverse dependency order.

---

## Relationships

- Reads table definitions from `models/db_models.py` (SQLModel classes).
- Writes to the same `data/linkedin_ads.db` used by `storage/database.py` and `storage/repository.py`.
- Configuration references `core/config.py` paths via `alembic.ini`.

---

## Common Commands

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Check current migration version
uv run alembic current

# Generate a new migration from model changes
uv run alembic revision --autogenerate -m "add new column"

# Show migration history
uv run alembic history

# Downgrade one step
uv run alembic downgrade -1

# Generate SQL without applying (offline mode)
uv run alembic upgrade head --sql
```

---

## Example: Adding a New Column

1. Add the column to the SQLModel class in `models/db_models.py`:

```python
class Campaign(SQLModel, table=True):
    # ... existing fields ...
    new_field: Optional[str] = None  # Add this
```

2. Generate the migration:

```bash
uv run alembic revision --autogenerate -m "add new_field to campaigns"
```

3. Review the generated migration file in `alembic/versions/`.

4. Apply it:

```bash
uv run alembic upgrade head
```

---

## Edge Cases & Tips

- **Existing database**: The initial migration uses `op.create_table()`, which will fail if tables already exist. For existing databases created by the raw SQL schema, the `CREATE TABLE IF NOT EXISTS` in `database.py` has already created them. Run `alembic stamp head` to mark the database as up-to-date without running the migration.
- **`prepend_sys_path = src`**: This is critical — without it, Alembic cannot import `linkedin_action_center` modules.
- **SQLite limitations**: SQLite does not support `ALTER TABLE DROP COLUMN` or `ALTER TABLE ALTER COLUMN`. Alembic handles this via batch operations (table recreation), but complex schema changes may require manual migration scripts.
- **Autogenerate**: `--autogenerate` compares the SQLModel metadata against the actual database schema. It's a best-effort tool — always review generated migrations before applying.

---

## Architecture / Flow

```
Developer changes models/db_models.py
    |
    └── alembic revision --autogenerate -m "description"
            ├── Reads SQLModel.metadata (target schema)
            ├── Reads current DB schema
            ├── Generates diff -> alembic/versions/XXXX_description.py
            └── Developer reviews and applies:
                    └── alembic upgrade head
                            └── Executes upgrade() on the database
```

---

## Advanced Notes

- Migration files are Python scripts with `upgrade()` and `downgrade()` functions. They use `alembic.op` for DDL operations.
- The `revision` field in each migration file creates a linked list (each migration points to its predecessor via `down_revision`).
- `alembic.ini` can be overridden with `--config` flag for different environments.
- For production deployments, always run `alembic upgrade head` before starting the application.
- The `sync_log` table was added in the initial migration (Sprint 3) alongside the other 6 tables.
