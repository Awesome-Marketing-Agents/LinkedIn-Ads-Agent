# Module: Database Engine & Session Factory

## Overview

`db.py` creates the SQLAlchemy engine connected to PostgreSQL and provides a session factory used as a FastAPI dependency. Also includes `init_db()` for dev convenience (creates all tables without Alembic).

---

## File Path

`backend/app/core/db.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `sqlalchemy.create_engine` | PostgreSQL engine creation |
| `sqlmodel.Session` | ORM session |
| `sqlmodel.SQLModel` | Table metadata for `init_db()` |
| `app.core.config.settings` | Database URI |

---

## Components

### `engine`

```python
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False, pool_pre_ping=True)
```

**Purpose**: Module-level SQLAlchemy engine singleton.

- `echo=False` — No SQL logging (use app logger instead)
- `pool_pre_ping=True` — Test connections before use to handle PostgreSQL restarts

### `init_db() -> None`

```python
def init_db() -> None:
    SQLModel.metadata.create_all(engine)
```

**Purpose**: Create all tables defined by SQLModel metadata. Dev convenience only — production uses Alembic migrations.

### `get_session() -> Generator[Session, None, None]`

```python
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

**Purpose**: Yield a SQLModel session. Note: this function exists but `core/deps.py:get_db()` is actually used as the FastAPI dependency.

---

## Code Snippet

```python
from app.core.db import engine, init_db
from sqlmodel import Session

# Dev: create tables
init_db()

# Manual session usage
with Session(engine) as session:
    session.exec(select(AdAccount)).all()
```

---

## Relationships

- **Used by**: `core/deps.py` imports `engine` for dependency injection
- **Used by**: `alembic/env.py` (indirectly via `settings.SQLALCHEMY_DATABASE_URI`)
- **Config from**: `core/config.py` provides the PostgreSQL connection string

---

## Known Gaps

- **No connection pool tuning** — Uses SQLAlchemy defaults (pool_size=5, max_overflow=10)
- **`get_session()` not used as dependency** — `core/deps.py:get_db()` duplicates this pattern
