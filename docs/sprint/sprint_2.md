# Sprint 2: Module Review & Refactoring

**Start Date**: February 19, 2026  
**Status**: In Progress

## 📋 Objectives

1. Review and refactor all core modules for clarity and separation of concerns
2. Add missing foundational modules (logging, error handling, analytics)
3. Integrate `rich` library for enhanced logging and error tracebacks
4. Write minimal unit tests for each module
5. Document module APIs and data flows
6. Prepare interfaces for LLM/brain integration

---

## 🔍 Module Review Findings

### ✅ Existing Modules

#### 1. **auth/** (Authentication & OAuth)
- **Files**: `manager.py`, `callback.py`
- **Status**: Well-structured
- **Findings**:
  - `AuthManager` handles token persistence, refresh, validation
  - `callback.py` uses FastAPI for OAuth callback server
  - Clear separation of concerns
  - **Refactor Needed**: 
    - Add proper error handling with rich tracebacks
    - Add logging for auth flow events
    - Extract token validation logic into separate helper
    - Add type hints to all methods

#### 2. **core/** (Configuration & Constants)
- **Files**: `config.py`, `constants.py`
- **Status**: Functional, needs enhancement
- **Findings**:
  - `config.py` loads env vars via `python-dotenv`
  - `constants.py` has API endpoints and scopes
  - **Refactor Needed**:
    - Validate config on load (fail fast if missing keys)
    - Add config validation helper
    - Consider using Pydantic for typed config

#### 3. **ingestion/** (LinkedIn API Client & Data Fetchers)
- **Files**: `client.py`, `fetchers.py`, `metrics.py`
- **Status**: Well-organized
- **Findings**:
  - `LinkedInClient` wraps HTTP calls with auth headers
  - `fetchers.py` has ad account, campaign, creative fetch logic
  - `metrics.py` fetches campaign/creative metrics and demographics
  - **Refactor Needed**:
    - Add retry logic for API calls
    - Better error messages with rich formatting
    - Add rate limit handling
    - Extract pagination logic to reusable helper

#### 4. **storage/** (SQLite Database & Snapshots)
- **Files**: `database.py`, `repository.py`, `snapshot.py`
- **Status**: Functional, uses raw SQL
- **Findings**:
  - `database.py` defines schema with 6 tables
  - `repository.py` has upsert/query logic with raw SQL
  - `snapshot.py` assembles structured JSON snapshots for analysis
  - **Refactor Needed** (HIGH PRIORITY):
    - Replace raw SQL with SQLAlchemy ORM
    - Add proper connection pooling
    - Add transaction management
    - Create model classes for type safety
    - Add data validation on insert

#### 5. **utils/** (Utilities)
- **Status**: Empty (just `__init__.py`)
- **Action**: Populate with shared helpers

#### 6. **analysis/** (Analytics & Insights)
- **Status**: Empty placeholder
- **Action**: Build analytics modules for LLM-ready insights

#### 7. **models/** (Data Models)
- **Status**: Empty placeholder
- **Action**: Add Pydantic or dataclass models for all entities

#### 8. **agent/** (LLM Brain - Future)
- **Status**: Placeholder with `utils/` subfolder
- **Action**: Reserved for future LLM integration

#### 9. **api/** (REST API Routes)
- **Status**: Has `routes/` subfolder
- **Action**: Consider extracting Flask routes from `main.py`

---

## 🛠️ Refactoring Action Plan

### Phase 1: Foundational Infrastructure (Current)

#### Task 1.1: Add `rich`-based Logging Module ✅
**File**: `src/linkedin_action_center/utils/logger.py`

Create a centralized logger using `rich`:
- Console logging with color/emoji
- File logging with rotation
- Structured log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Context-aware logging (add module name, timestamp)
- Rich tracebacks for exceptions

#### Task 1.2: Add Error Handling Module
**File**: `src/linkedin_action_center/utils/errors.py`

Define custom exception classes:
- `LinkedInAPIError` (base for all API errors)
- `AuthenticationError`
- `RateLimitError`
- `ValidationError`
- `ConfigurationError`

Add error formatting with rich.

#### Task 1.3: Add Config Validation
**File**: `src/linkedin_action_center/core/config.py` (update)

- Validate all required env vars on load
- Fail fast with clear error message if missing
- Optional: Use Pydantic `BaseSettings` for typed config

---

### Phase 2: Module Refactoring (Next)

#### Task 2.1: Refactor `auth/`
- Add logging to all methods
- Replace print statements with logger calls
- Add rich tracebacks for OAuth errors
- Extract token validation into `utils/token_validator.py`

#### Task 2.2: Refactor `ingestion/`
- Add retry logic with exponential backoff
- Add rate limit detection and handling
- Extract pagination helper to `utils/pagination.py`
- Replace print statements with logger calls

#### Task 2.3: Refactor `storage/` (HIGH PRIORITY)
- **Replace raw SQL with SQLAlchemy ORM**
- Create model classes in `models/`
- Add proper connection pooling
- Add transaction context managers
- Add data validation on insert

---

### Phase 3: Testing & Documentation (Later)

#### Task 3.1: Write Unit Tests
- Use `pytest`
- Create `tests/` folder at project root
- Add tests for each module (aim for >70% coverage)
- Mock external dependencies (LinkedIn API, DB)

#### Task 3.2: Update Documentation
- Update `docs/research/arch.md` with module APIs
- Add docstrings to all classes/functions
- Create API reference docs

---

## 📦 New Modules to Add

### 1. `utils/logger.py` (Logging with rich)
### 2. `utils/errors.py` (Custom exceptions)
### 3. `utils/pagination.py` (Pagination helper)
### 4. `utils/retry.py` (Retry logic with backoff)
### 5. `utils/validators.py` (Data validation helpers)
### 6. `models/entities.py` (Pydantic/dataclass models)
### 7. `analysis/metrics.py` (Analytics & insights)

---

## 🧪 Testing Strategy

- **Unit tests**: Test each module in isolation
- **Integration tests**: Test module interactions (e.g., client → fetcher → storage)
- **End-to-end tests**: Test full workflows (auth → sync → analyze)

---

## 📝 Next Steps

1. ✅ Create `utils/logger.py` with rich integration
2. ⏳ Integrate logger into existing modules
3. ⏳ Add error handling module
4. ⏳ Refactor storage layer to use SQLAlchemy
5. ⏳ Write unit tests
6. ⏳ Update documentation

---

## 🎯 Success Criteria

- All modules use centralized logging (no more print statements)
- All exceptions use rich tracebacks
- Storage layer uses ORM (no raw SQL)
- All modules have type hints
- Core modules have >70% test coverage
- Documentation is up-to-date and accurate
