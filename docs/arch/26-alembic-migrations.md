# Module: Alembic Database Migrations

## Overview

Alembic manages PostgreSQL schema versioning with three migrations: initial schema creation, metric column additions, and creative content name enrichment.

---

## File Paths

- `backend/alembic/env.py`
- `backend/alembic/versions/0001_initial_schema.py`
- `backend/alembic/versions/0002_add_missing_columns.py`
- `backend/alembic/versions/0003_add_content_name.py`

---

## Configuration (env.py)

```python
from app.core.config import settings
from app.models import *  # Ensure all models registered

target_metadata = SQLModel.metadata
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)
```

**Key details**:
- `sys.path.insert(0, ...)` adds backend directory to path
- `from app.models import *` triggers all SQLModel table registrations
- Database URL comes from `settings.SQLALCHEMY_DATABASE_URI` (PostgreSQL)
- Uses `NullPool` for online migrations (no connection pooling)

---

## Migrations

### 0001: Initial Schema

**Revision**: `0001` | **Revises**: — | **Tables created**: 7

Creates all tables: `ad_accounts`, `campaigns`, `creatives`, `campaign_daily_metrics`, `creative_daily_metrics`, `audience_demographics`, `sync_log`.

### 0002: Add Missing Columns

**Revision**: `0002` | **Revises**: `0001`

Adds `follows`, `leads`, `opens`, `sends` columns (with `server_default="0"`) to both `campaign_daily_metrics` and `creative_daily_metrics`.

Adds `serving_hold_reasons` column to `creatives`.

### 0003: Add Content Name

**Revision**: `0003` | **Revises**: `0002`

Adds `content_name` column (Text) to `creatives` table for human-readable creative labels.

---

## Commands

```bash
cd backend

# Apply all migrations
alembic upgrade head

# Check current revision
alembic current

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one step
alembic downgrade -1
```

---

## Relationships

- **Config from**: `core/config.py` for database URI
- **Models from**: `models/__init__.py` for table metadata
