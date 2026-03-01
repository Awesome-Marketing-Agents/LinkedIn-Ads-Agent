# Module: Test Infrastructure

## Overview

The test suite uses pytest with SQLite in-memory databases (via `StaticPool`) to test CRUD operations, routes, auth logic, error handling, and the LinkedIn client. FastAPI's dependency injection is overridden to use test sessions.

---

## File Paths

- `backend/tests/conftest.py`
- `backend/tests/test_auth.py`
- `backend/tests/test_client.py`
- `backend/tests/test_crud.py`
- `backend/tests/test_errors.py`
- `backend/tests/test_routes.py`

---

## Fixtures (conftest.py)

### `engine_fixture`

```python
@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
```

**Purpose**: In-memory SQLite engine shared across test threads.

**Why `StaticPool`**: FastAPI's `TestClient` uses threads internally. Without `StaticPool`, each thread would get a different in-memory database. `StaticPool` ensures all threads share the same connection.

**Why `check_same_thread=False`**: SQLite normally restricts access to the creating thread. This flag allows cross-thread access needed for `TestClient`.

### `session_fixture`

Yields a `Session(engine)` for direct CRUD testing.

### `client_fixture`

```python
@pytest.fixture(name="client")
def client_fixture(engine):
    def get_test_db():
        with Session(engine) as session:
            yield session
    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
```

**Purpose**: FastAPI `TestClient` with database dependency override.

### `mock_tokens`

Pre-built token dict with valid expiry timestamps for auth testing.

---

## Test Files

| File | Tests | Focus |
|------|-------|-------|
| `test_auth.py` | Auth status, token management | AuthManager behavior |
| `test_client.py` | LinkedIn API client | HTTP client logic |
| `test_crud.py` | Database operations | Upserts, queries, pagination |
| `test_errors.py` | Exception hierarchy | Error creation, attributes |
| `test_routes.py` | API endpoints | Route responses, status codes |

---

## Running Tests

```bash
cd backend && pytest                    # All tests
cd backend && pytest -v                 # Verbose
cd backend && pytest tests/test_crud.py # Single file
cd backend && pytest -k "test_upsert"   # Pattern match
```

---

## Design Decisions

- **SQLite for tests**: Tests use SQLite instead of PostgreSQL for speed and zero-config. PostgreSQL-specific features (like `insert().on_conflict_do_update()`) are not testable this way.
- **No test database setup**: No fixtures, Docker, or migrations needed — tables are created from SQLModel metadata.
- **Dependency override**: FastAPI's `dependency_overrides` cleanly swaps the production database session for the test session.

---

## Known Gaps

- **PostgreSQL upserts untested** — SQLite doesn't support `ON CONFLICT DO UPDATE` with `insert()` from `sqlalchemy.dialects.postgresql`
- **No integration tests** — Tests mock the LinkedIn API rather than calling it
