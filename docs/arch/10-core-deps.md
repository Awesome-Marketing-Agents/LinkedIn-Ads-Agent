# Module: FastAPI Dependencies

## Overview

`deps.py` defines FastAPI dependency injection functions used across all routes. `get_db()` yields database sessions and `get_auth()` creates `AuthManager` instances.

---

## File Path

`backend/app/core/deps.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `sqlmodel.Session` | Database session type |
| `app.core.db.engine` | SQLAlchemy engine for session creation |
| `app.core.security.AuthManager` | OAuth token manager |

---

## Components

### `get_db() -> Generator[Session, None, None]`

```python
def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

**Purpose**: Yield a database session for the duration of a request. The session is automatically closed when the request completes.

**Usage in routes**:
```python
@router.get("/campaigns")
def campaigns_list(session: Session = Depends(get_db)):
    return get_campaigns(session)
```

### `get_auth() -> AuthManager`

```python
def get_auth() -> AuthManager:
    return AuthManager()
```

**Purpose**: Create a fresh `AuthManager` instance for each request. The manager loads tokens from disk on initialization.

**Usage in routes**:
```python
@router.get("/status")
async def auth_status(auth: AuthManager = Depends(get_auth)):
    return auth.token_status()
```

---

## Code Snippet

```python
from fastapi import Depends
from sqlmodel import Session
from app.core.deps import get_db, get_auth
from app.core.security import AuthManager

@router.get("/example")
def example(session: Session = Depends(get_db), auth: AuthManager = Depends(get_auth)):
    # session is auto-closed after response
    # auth is a fresh instance with current tokens
    pass
```

---

## Relationships

- **Used by**: All route modules via `Depends(get_db)` and `Depends(get_auth)`
- **Also used by**: `routes/sync.py` passes `get_db` function reference to `run_sync()` for background session creation
- **Overridden in tests**: `conftest.py` overrides `get_db` with SQLite in-memory session

---

## Known Gaps

- `get_auth()` creates a new `AuthManager` per request, re-reading tokens from disk each time
