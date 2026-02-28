# Ingestion Pipeline Optimization
### LinkedIn Ads Action Center — Sprint 3 Planning Document

**Document Type:** Dual-audience — Executive Summary (PM) + Technical Specification (Dev)  
**Sprint:** 3 — Immediate Priority  
**Status:** Ready for sprint planning  
**Last Updated:** February 28, 2026  
**Authors:** Engineering Team

---

## How to Read This Document

| If you are... | Read... |
|---|---|
| **Product Manager** | Section 1 and 2 only — ~5 min read |
| **Developer** | All sections — technical spec starts at Section 3 |
| **Both in a meeting** | Start with Section 2 diagram, then decide scope together |

---

# PART 1 — EXECUTIVE SUMMARY
*For Product Managers. Skip to Part 2 for the technical diagram.*

---

## 1.1 What Is the Ingestion Pipeline?

Every insight, recommendation, and "play" the Action Center surfaces to users comes from data we pull from LinkedIn's Ads API. The **ingestion pipeline** is the system that fetches that data, processes it, and stores it so our AI agents can analyze it.

Think of it as the nervous system of the product. If it's slow, unreliable, or fetching the same data repeatedly, everything downstream — the agents, the dashboard, the plays — is degraded.

---

## 1.2 What Are the Problems Today?

We have three distinct problems. They are independent but compound each other.

**Problem 1 — Duplicate Data (High Severity)**

Every time a user clicks "Sync" or a scheduled sync runs, the system fetches all data from LinkedIn from scratch and writes it to the database again, regardless of whether anything has changed. There is no check for "have we already fetched this today?" and no deduplication at the write layer. The result: the same campaign data exists multiple times in our database, metrics rows are duplicated, and our analytics are unreliable until we happen to overwrite the right rows.

*Business impact:* Agent analysis runs on dirty data. Play recommendations may be based on duplicated or stale rows. This will worsen as we add more agents.

**Problem 2 — No Type Safety or Data Contracts (Medium Severity)**

Data moves through the system as raw Python dictionaries with no enforced shape. LinkedIn's API returns camelCase JSON; our database uses snake_case; our agents will eventually need typed objects. Currently there is nothing validating that a campaign object has the fields we expect, that a budget value is actually a number, or that a date range is valid before it gets written to the database.

*Business impact:* Silent data corruption is invisible until an agent produces a wrong recommendation. Debugging takes hours because there is no clear moment where bad data gets caught and logged.

**Problem 3 — Tech Stack Mismatch (Medium Severity)**

The current stack (Flask + raw SQL + `requests`) was appropriate for a proof of concept. Sprint 1 established the structure. Sprint 2 added logging and error handling. But the stack is now misaligned with where we are going: a multi-tenant SaaS with LLM agents reading structured data. We have already started using FastAPI in one place (the OAuth callback). The storage layer still uses hardcoded SQL strings and has no migration system — meaning any schema change is a manual, error-prone operation.

*Business impact:* Every sprint that builds on this foundation (agents, optimization execution, multi-tenant) carries the technical debt forward. The cost of migration increases the longer we wait.

---

## 1.3 What Are We Proposing to Fix?

We are proposing a **phased, iterative modernization** — not a rewrite. Each phase delivers working software and can be shipped independently. The full migration spans Sprint 3 through Sprint 5. Sprint 3 tackles the highest-severity problems first.

| Phase | Sprint | What Gets Fixed | User-Visible Impact |
|---|---|---|---|
| **Phase 1** — Freshness Gate + Deduplication | Sprint 3 | Sync no longer fetches duplicate data | Faster syncs, reliable analytics |
| **Phase 2** — Pydantic Models + Type Safety | Sprint 3 | Data validated before it touches the DB | Fewer silent bugs, LLM-ready data shapes |
| **Phase 3** — SQLModel + Alembic (ORM + Migrations) | Sprint 4 | Replace hardcoded SQL with typed ORM | Safe schema changes, no raw SQL |
| **Phase 4** — FastAPI Full Migration + Async Client | Sprint 5 | Replace Flask, add async ingestion | Concurrent syncs, multi-tenant ready |

---

## 1.4 What Are We NOT Doing in Sprint 3?

To set correct expectations: Sprint 3 does **not** include:

- Redis caching layer (Phase 4 — after async client is in place)
- S3/GCS raw storage (Phase 4 — depends on async architecture)
- Multi-tenant per-account isolation (Phase 4)
- Full PostgreSQL migration (Phase 4 — SQLite remains for Sprint 3–4)
- LLM agent integration (separate workstream)

These are deliberately deferred. Doing them now would require a bigger bang change that risks destabilizing the working codebase before Sprint 3 goals are delivered.

---

## 1.5 Sprint 3 Success Criteria (PM Checklist)

- [ ] Running sync twice in a row does not create duplicate rows in the database
- [ ] A sync that finds no new data completes in under 5 seconds (freshness gate working)
- [ ] A validation error in incoming LinkedIn data produces a clear, logged error — not a silent failure
- [ ] All six database tables have corresponding Pydantic/SQLModel models
- [ ] No hardcoded SQL strings remain in `storage/repository.py`
- [ ] Alembic is initialized and the current schema is captured as migration `0001`

---

# PART 2 — ARCHITECTURE
*Both audiences. Start here if you are short on time.*

---

## 2.1 Current State vs. Target State

### Current Architecture (Sprint 2 End State)

```
User / Cron
    │
    ▼
cli.py / main.py (Flask)
    │
    ▼
AuthManager ──► tokens.json
    │
    ▼
LinkedInClient (requests — synchronous)
    │
    ├── fetchers.py ──► raw dict
    └── metrics.py  ──► raw dict
              │
              ▼
    snapshot.py (assemble dict)
              │
              ▼
    repository.py
    (raw SQL — INSERT OR REPLACE)
              │
              ▼
    SQLite (linkedin_ads.db)
```

**What's missing:**
- No freshness check before hitting LinkedIn API
- `INSERT OR REPLACE` is not true upsert — it deletes + reinserts, breaking row history
- Raw dicts with no validation between LinkedIn API and database
- No schema migration system — changing a table requires manual SQL
- Synchronous `requests` library blocks the entire process during API calls
- Single-file schema defined as a string constant in `database.py`

---

### Target Architecture (Sprint 3–5 End State)

```
User / APScheduler (cron) / FastAPI endpoint (on-demand)
    │
    ▼
┌─────────────────────────────────────┐
│  Ingestion Orchestrator             │
│  - Freshness gate (check last sync) │
│  - Per-account run tracking         │
└─────────────────────────────────────┘
    │
    ├── Cache HIT?  ──► Return cached snapshot, skip API
    │
    └── Cache MISS?
              │
              ▼
    LinkedInAsyncClient (httpx — async)
    + Token Bucket Rate Limiter
              │
    ┌─────────┴──────────┐
    │                    │
    ▼                    ▼
fetchers.py          metrics.py
(async)              (async, batched)
    │                    │
    └─────────┬──────────┘
              ▼
    ┌─────────────────────┐
    │  Pydantic Models    │  ◄── Validation happens HERE
    │  (entities.py)      │      Bad data caught, logged, skipped
    └─────────────────────┘
              │
    ┌─────────┴──────────────────────┐
    │                                │
    ▼                                ▼
S3/GCS Raw Store              SQLModel ORM
(raw JSON, gzipped)           (PostgreSQL — Phase 4)
(audit / LLM context)         (Alembic migrations)
```

---

## 2.2 Data Flow: What Happens on a Sync

```
SYNC TRIGGERED (scheduled or on-demand)
    │
    ├─► Check: when was the last successful sync for this account?
    │       └─► Last sync < 4 hours ago AND trigger = "scheduled"
    │               └─► SKIP — return cached data, log "freshness gate hit"
    │
    └─► Last sync > 4 hours OR trigger = "on_demand"
            │
            ▼
        Fetch from LinkedIn API (async, concurrent)
            ├── accounts (1 call)
            ├── campaigns (1 call per account)
            ├── creatives (1 call per account)
            ├── campaign metrics (batched, 20 campaigns per call)
            ├── creative metrics (batched)
            └── demographics (batched)
            │
            ▼
        Validate each response through Pydantic models
            ├── Valid   ──► Continue to storage
            └── Invalid ──► Log error, skip that record, continue run
            │
            ▼
        Write raw JSON to S3 (gzipped, timestamped)
            │
            ▼
        Upsert to PostgreSQL via SQLModel
        (true upsert: update if exists, insert if new — no delete/reinsert)
            │
            ▼
        Update sync log: account_id, timestamp, rows written, errors
            │
            ▼
        DONE — downstream agents can query fresh data
```

---

# PART 3 — TECHNICAL SPECIFICATION
*For developers. This is the complete handoff for Sprint 3.*

---

## 3.1 Sprint 3 Scope (What Gets Built)

Sprint 3 delivers **Phase 1 + Phase 2** from the roadmap. Specifically:

| Task | File(s) | Priority | Estimated Effort |
|---|---|---|---|
| T1 — Sync log table + freshness gate | `storage/database.py`, `repository.py` | P0 | 0.5 day |
| T2 — Fix upsert logic (true upsert) | `storage/repository.py` | P0 | 0.5 day |
| T3 — Pydantic models for all entities | `models/entities.py` (new) | P0 | 1 day |
| T4 — Validate in snapshot assembly | `storage/snapshot.py` | P1 | 0.5 day |
| T5 — SQLModel models (mirrors Pydantic) | `models/db_models.py` (new) | P1 | 1 day |
| T6 — Alembic initialization + migration 0001 | `alembic/` (new) | P1 | 0.5 day |
| T7 — Replace raw SQL in repository | `storage/repository.py` | P1 | 1 day |
| T8 — Config migration to Pydantic BaseSettings | `core/config.py` | P2 | 0.5 day |

**Total estimated: ~5.5 dev days**

---

## 3.2 Problem 1 Fix — Freshness Gate + True Upsert

### Root Cause

Two separate bugs compound each other:

**Bug A — No freshness gate.** `cli.py sync` and the Flask `/sync` route call the full fetch pipeline unconditionally every time. There is no check against when data was last fetched. LinkedIn API is hit every time, regardless of data freshness.

**Bug B — `INSERT OR REPLACE` is not an upsert.** SQLite's `INSERT OR REPLACE` works by deleting the existing row and inserting a new one. This means: (a) `fetched_at` timestamps on unchanged records are overwritten on every sync — poisoning our "when did this change?" audit trail, and (b) if a row has foreign key children, SQLite deletes the parent and all cascaded children, then re-inserts. Even with WAL mode, this creates unnecessary write amplification.

### Fix A — Sync Log Table

Add a `sync_log` table to `database.py`:

```sql
CREATE TABLE IF NOT EXISTS sync_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id    TEXT    NOT NULL,
    started_at    TEXT    NOT NULL,
    finished_at   TEXT,
    status        TEXT    NOT NULL DEFAULT 'running',  -- running | success | partial | failed | skipped
    trigger       TEXT    NOT NULL DEFAULT 'scheduled', -- scheduled | on_demand
    campaigns_fetched  INTEGER DEFAULT 0,
    creatives_fetched  INTEGER DEFAULT 0,
    api_calls_made     INTEGER DEFAULT 0,
    errors        TEXT,   -- JSON array of error strings
    UNIQUE(account_id, started_at)
);
```

**Freshness gate logic in `repository.py`:**

```python
def should_sync(account_id: str, force: bool = False) -> tuple[bool, str]:
    """
    Returns (should_sync: bool, reason: str).
    Checks last successful sync timestamp against FRESHNESS_TTL_MINUTES.
    force=True bypasses the gate (on-demand trigger).
    """
    FRESHNESS_TTL_MINUTES = 240  # 4 hours — configurable via env var

    if force:
        return True, "on_demand_force_refresh"

    last_sync = get_last_successful_sync(account_id)  # queries sync_log
    if last_sync is None:
        return True, "no_prior_sync"

    age_minutes = (datetime.now(timezone.utc) - last_sync).total_seconds() / 60
    if age_minutes > FRESHNESS_TTL_MINUTES:
        return True, f"data_stale_{age_minutes:.0f}min"

    return False, f"data_fresh_{age_minutes:.0f}min"
```

### Fix B — True Upsert Strategy

Replace all `INSERT OR REPLACE` with proper upsert semantics. In SQLite this is `INSERT INTO ... ON CONFLICT(id) DO UPDATE SET ...`. In PostgreSQL (Phase 4) this becomes `INSERT ... ON CONFLICT DO UPDATE`.

**Pattern for every upsert in `repository.py`:**

```sql
-- BEFORE (wrong — deletes then reinserts)
INSERT OR REPLACE INTO campaigns (id, name, status, ...) VALUES (?, ?, ?, ...)

-- AFTER (correct — updates only changed fields, preserves created_at)
INSERT INTO campaigns (id, name, status, fetched_at, ...)
VALUES (?, ?, ?, ?, ...)
ON CONFLICT(id) DO UPDATE SET
    name       = excluded.name,
    status     = excluded.status,
    fetched_at = excluded.fetched_at
    -- created_at is NOT updated — preserves original insert time
```

This is the key insight: `fetched_at` updates on every sync (we touched this record). `created_at` never updates (when did we first see it). Currently neither field is handled correctly because `INSERT OR REPLACE` nukes both.

### Fix C — Idempotency Contract

Every sync run must be idempotent. Running the same sync twice must produce the same database state. This requires:

1. Freshness gate prevents the second run from hitting the API at all (if within TTL)
2. If a second run does execute (force refresh), the `ON CONFLICT DO UPDATE` upsert ensures no duplicates
3. Metrics rows use composite primary key `(campaign_id, date)` — same date, same campaign always updates the same row

---

## 3.3 Problem 2 Fix — Pydantic Models + Type Safety

### Root Cause

Data flows through the system as `dict[str, Any]` from the LinkedIn API response all the way to the database write. There is no validation layer. A missing field, a `None` where a number is expected, or a malformed URN silently passes through and either causes a crash deep in the pipeline or writes corrupt data to SQLite.

### Model Architecture

Two model layers, clearly separated:

```
Layer 1 — API Response Models (ingestion/models.py)
    Purpose: Validate and parse raw LinkedIn API JSON
    Base class: pydantic.BaseModel
    Naming: LinkedInCampaign, LinkedInCreative, LinkedInAnalyticsRow
    Direction: LinkedIn API JSON ──► Python object

Layer 2 — Database Models (models/db_models.py)
    Purpose: ORM table definitions for SQLModel/PostgreSQL
    Base class: sqlmodel.SQLModel, table=True
    Naming: Campaign, Creative, CampaignDailyMetric
    Direction: Python object ──► Database row
```

Never mix these two layers. A `LinkedInCampaign` is not a `Campaign`. You parse from the API using the first, transform, then write to DB using the second.

### Key Model Design Decisions

**Aliases for camelCase → snake_case translation:**

LinkedIn returns `dailyBudget`, `bidStrategy`, `audienceNetwork`. Your database stores `daily_budget`, `bid_strategy`, `audience_network`. Pydantic handles this with `model_config = ConfigDict(populate_by_name=True)` and `Field(alias="dailyBudget")`. No manual key translation needed anywhere.

**Strict vs. lenient parsing:**

Use `model_config = ConfigDict(extra="ignore")` on API models. LinkedIn adds new fields to responses without warning. Strict parsing would break on new fields. Lenient parsing ignores them and only validates the fields you declared.

**Partial failure handling:**

When validating a batch of 50 creatives and 3 fail validation, the pipeline should: log the 3 failures with full context (which creative ID, which field, what value was received), and continue processing the 47 valid ones. Never fail the entire batch for one bad record.

```python
# Pattern for all validation points in snapshot.py
valid_campaigns = []
for raw in raw_campaigns:
    try:
        valid_campaigns.append(LinkedInCampaign.model_validate(raw))
    except ValidationError as e:
        logger.warning(f"Validation failed for campaign {raw.get('id')}: {e}")
        # Do NOT raise — log and continue
```

### Entity Models Required (Sprint 3)

| Model Name | Layer | Source | Key Fields |
|---|---|---|---|
| `LinkedInAccount` | API | `/adAccounts` | id, name, status, currency, type |
| `LinkedInCampaign` | API | `/adCampaigns` | id, account_id, name, status, bid_strategy, daily_budget, audience_expansion_enabled, offsite_delivery_enabled |
| `LinkedInCreative` | API | `/adCreatives` | id, campaign_id, intended_status, is_serving |
| `LinkedInAnalyticsRow` | API | `/adAnalytics` | campaign_id, date, impressions, clicks, cost, conversions |
| `LinkedInDemographicRow` | API | `/adAnalytics` (pivot) | account_id, pivot_type, segment, impressions, clicks |
| `Account` | DB | — | mirrors LinkedInAccount + created_at, fetched_at |
| `Campaign` | DB | — | mirrors LinkedInCampaign + created_at, fetched_at |
| `Creative` | DB | — | mirrors LinkedInCreative + created_at, fetched_at |
| `CampaignDailyMetric` | DB | — | campaign_id, date, impressions, clicks, cost, ctr, cpc |
| `CreativeDailyMetric` | DB | — | creative_id, campaign_id, date, impressions, clicks, ctr |
| `AudienceDemographic` | DB | — | account_id, pivot_type, segment, impressions, clicks |
| `SyncLog` | DB | — | account_id, started_at, finished_at, status, trigger, errors |

### Computed Fields at Model Level

CTR, CPC, and CPL should be computed properties on the DB model — not stored as raw numbers that can get out of sync with their source metrics:

```python
# In CampaignDailyMetric (SQLModel)
@property
def ctr(self) -> float | None:
    if self.impressions and self.impressions > 0:
        return self.clicks / self.impressions
    return None

@property
def cpc(self) -> float | None:
    if self.clicks and self.clicks > 0:
        return self.cost / self.clicks
    return None
```

This eliminates the current pattern of pre-computing CTR/CPC in `snapshot.py` and storing them as columns — they were always derived values masquerading as raw data.

---

## 3.4 Problem 3 Fix — SQLModel + Alembic

### Why SQLModel over Raw SQLAlchemy

SQLModel = SQLAlchemy Core + Pydantic v2. One class definition serves as both the ORM table model AND the Pydantic validation model. This eliminates the current duplication between the schema in `database.py` (SQL string) and the field mapping in `repository.py` (Python dict).

**Before (current pattern):**
```
database.py    → SQL string defining table shape
repository.py  → Python dict hardcoded to match that shape
snapshot.py    → Python dict hardcoded to match repository's expectations
```
Three places that must stay in sync manually. When LinkedIn adds a field, you touch three files and hope you didn't miss one.

**After (SQLModel):**
```
models/db_models.py → SQLModel class (ONE definition)
    ↓ Alembic reads this and generates migration SQL automatically
    ↓ Repository uses model class — no hardcoded field names
    ↓ Snapshot assembler creates model instances — Pydantic validates on construction
```
One definition. One place to change. Alembic generates the SQL.

### Alembic Setup (Sprint 3 Task)

Initialize Alembic in the project:

```
project root/
├── alembic/
│   ├── env.py          ← configure to import SQLModel metadata
│   ├── script.py.mako  ← migration template
│   └── versions/
│       └── 0001_initial_schema.py  ← auto-generated from current SQLite schema
├── alembic.ini         ← points to DATABASE_URL env var
```

**Migration workflow going forward:**

```bash
# Developer adds a field to a SQLModel class, then:
alembic revision --autogenerate -m "add_creative_format_field"
# Alembic diffs the model vs. DB and generates the migration SQL
alembic upgrade head
# Applies the migration — no manual SQL, no risk of missing a column
```

This is the key unlock for future sprints: when the LLM agents need a new column (e.g., `fatigue_score`, `embedding vector`), it's a 2-line change in the model + one Alembic command. Currently it requires manually editing the SQL string in `database.py` and hoping nothing breaks.

### Repository Rewrite Pattern

Every raw SQL function in `repository.py` gets replaced with a SQLModel session pattern:

```python
# BEFORE — fragile, hardcoded, no type safety
def _upsert_campaign(cur, account_id: str, camp: dict, now: str):
    cur.execute("""
        INSERT OR REPLACE INTO campaigns
        (id, account_id, name, status, ...) VALUES (?, ?, ?, ?, ...)
    """, (camp["id"], account_id, camp.get("name"), camp.get("status"), ...))

# AFTER — typed, validated, migration-safe
def upsert_campaign(session: Session, campaign: Campaign) -> None:
    existing = session.get(Campaign, campaign.id)
    if existing:
        # Only update mutable fields — preserve created_at
        existing.name       = campaign.name
        existing.status     = campaign.status
        existing.fetched_at = campaign.fetched_at
        # ... other mutable fields
    else:
        session.add(campaign)
    # session.commit() called by caller — not here
    # Repository functions do NOT commit. Callers control transactions.
```

The last point is critical and currently violated: `repository.py` calls `conn.commit()` inside individual upsert functions. This means a partial failure leaves the database in an inconsistent state. The fix: repository functions add/modify objects in the session. The caller (the sync orchestrator) commits once at the end, or rolls back the entire sync on failure.

---

## 3.5 Config Migration — Pydantic BaseSettings

`core/config.py` currently loads env vars via `python-dotenv` with no validation. Missing `LINKEDIN_CLIENT_ID`? You get a `None` that travels silently until it causes a cryptic `401 Unauthorized` from LinkedIn's API 10 steps later.

Replace with Pydantic `BaseSettings`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    linkedin_client_id:     str
    linkedin_client_secret: str
    linkedin_redirect_uri:  str
    oauth_state:            str  = "supersecretstate"
    database_url:           str  = "sqlite:///data/linkedin_ads.db"
    freshness_ttl_minutes:  int  = 240
    log_level:              str  = "INFO"

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()  # Raises ValidationError immediately on startup if required vars missing
```

`settings` is a module-level singleton. Every other module imports `from core.config import settings`. No more `os.getenv()` scattered across files.

---

## 3.6 Module File Map — Sprint 3 Changes

```
src/linkedin_action_center/
│
├── core/
│   └── config.py                ← MODIFY: migrate to Pydantic BaseSettings
│
├── models/                      ← NEW DIRECTORY
│   ├── __init__.py
│   ├── api_models.py            ← NEW: Pydantic models for LinkedIn API responses
│   └── db_models.py             ← NEW: SQLModel ORM models (table definitions)
│
├── ingestion/
│   ├── client.py                ← MINOR: use settings.linkedin_* instead of hardcoded
│   ├── fetchers.py              ← MINOR: validate output through api_models
│   └── metrics.py               ← MINOR: validate output through api_models
│
├── storage/
│   ├── database.py              ← MODIFY: add sync_log table, remove hardcoded _SCHEMA string
│   ├── repository.py            ← MAJOR REWRITE: replace raw SQL with SQLModel session pattern
│   └── snapshot.py              ← MODIFY: validate through api_models before assembly
│
└── alembic/                     ← NEW DIRECTORY
    ├── env.py
    ├── alembic.ini
    └── versions/
        └── 0001_initial_schema.py
```

**Files NOT touched in Sprint 3:**

- `auth/` — well-structured, no changes needed this sprint
- `main.py` (Flask) — Flask → FastAPI migration is Phase 4
- `cli.py` — interface layer, no changes needed until Phase 4
- `ingestion/client.py` — async migration is Phase 4
- `utils/logger.py`, `utils/errors.py` — completed in Sprint 2

---

## 3.7 Migration Phases — Full Roadmap

### Phase 1 — Freshness Gate + True Upsert (Sprint 3, P0)
**Goal:** Stop fetching and writing duplicate data.  
**Changes:** `sync_log` table, `should_sync()` gate, `ON CONFLICT DO UPDATE` in all upserts.  
**Risk:** Low. Additive changes only. Existing behavior unchanged if gate is bypassed.  
**Rollback:** Remove `should_sync()` call — pipeline behaves exactly as before.

---

### Phase 2 — Pydantic Models + Type Safety (Sprint 3, P1)
**Goal:** Validate all data before it touches the database.  
**Changes:** New `models/` directory, validation injected in `snapshot.py`.  
**Risk:** Low-Medium. Validation may surface data issues that were previously silent — treat these as bugs discovered, not bugs introduced.  
**Rollback:** Remove validation calls — pipeline passes raw dicts as before.

---

### Phase 3 — SQLModel + Alembic (Sprint 4)
**Goal:** Replace hardcoded SQL with typed ORM. Enable safe schema migrations.  
**Changes:** `storage/repository.py` full rewrite, `alembic/` init, `models/db_models.py`.  
**Risk:** Medium. Repository is the most-used module. Requires thorough integration tests before merge.  
**Prerequisite:** Phase 2 complete (models exist before ORM uses them).  
**Rollback:** Keep old `repository.py` as `repository_legacy.py` until Phase 3 is verified stable.

---

### Phase 4 — FastAPI + httpx Async + PostgreSQL (Sprint 5)
**Goal:** Replace Flask with FastAPI. Replace `requests` with async `httpx`. Migrate SQLite → PostgreSQL.  
**Changes:** `main.py` → `api/` FastAPI app, `ingestion/client.py` → async, `storage/database.py` → PostgreSQL connection, env var `DATABASE_URL` switches DB.  
**Risk:** High. Multiple simultaneous changes. Must be done behind a feature flag or parallel deployment.  
**Prerequisite:** Phase 3 complete (Alembic handles the SQLite → PostgreSQL schema migration).  
**New capabilities unlocked:** Concurrent multi-account syncs, Redis freshness cache, S3 raw storage, on-demand API endpoint.

---

## 3.8 What Phase 4 Unlocks (Preview for Sprint 5 Planning)

Once async + PostgreSQL are in place, the following become straightforward additions:

**Redis freshness cache:** Instead of querying `sync_log` on every run, check a Redis key `freshness:{account_id}` with a TTL. Expires automatically — no cleanup logic needed.

**S3 raw storage:** Every API response lands in S3 as `raw/{account_id}/{YYYY-MM-DD}/{endpoint}.json.gz` before any transformation. Three benefits: LLM agents can fetch full raw context without hitting LinkedIn API; reprocessing after a bug fix requires no re-ingestion; compliance audit trail is immutable.

**On-demand FastAPI endpoint:** `POST /api/v1/accounts/{account_id}/sync?force=true` triggers a sync for one account and returns a `run_id`. The dashboard polls `GET /api/v1/runs/{run_id}` for status. Clean separation of trigger from execution.

**Concurrent multi-account:** With async httpx, 10 accounts can sync simultaneously in the same event loop. LinkedIn's rate limits are respected via a per-account token bucket, not a global lock.

---

## 3.9 Dependency Changes for Sprint 3

Add to `pyproject.toml`:

```toml
[project.dependencies]
# Existing
requests = ">=2.31"
flask = ">=3.0"
rich = ">=13.0"
python-dotenv = ">=1.0"

# Sprint 3 additions
pydantic = ">=2.6"
pydantic-settings = ">=2.2"   # BaseSettings for config
sqlmodel = ">=0.0.16"          # SQLModel ORM
alembic = ">=1.13"             # Database migrations
sqlalchemy = ">=2.0"           # SQLModel dependency (explicit)

# Phase 4 (do NOT add in Sprint 3)
# httpx = ">=0.27"
# asyncpg = ">=0.29"
# fastapi = ">=0.110"
# redis = ">=5.0"
```

---

## 3.10 Testing Requirements for Sprint 3

Every Sprint 3 change requires a corresponding test. No exceptions.

| Test | What to Verify |
|---|---|
| `test_freshness_gate_skip` | Sync triggered twice within TTL — second run returns `skipped`, makes 0 API calls |
| `test_freshness_gate_force` | Force refresh bypasses TTL gate — API is called regardless |
| `test_upsert_no_duplicate` | Same campaign upserted twice — `SELECT COUNT(*)` returns 1, not 2 |
| `test_upsert_preserves_created_at` | Campaign upserted twice — `created_at` unchanged on second upsert |
| `test_pydantic_valid_campaign` | Valid LinkedIn API response parses without error |
| `test_pydantic_missing_field` | API response with missing required field raises `ValidationError` |
| `test_pydantic_extra_field_ignored` | API response with unknown extra field parses successfully (future-proofing) |
| `test_partial_batch_failure` | Batch of 10 campaigns with 2 invalid — 8 written to DB, 2 logged as errors, no exception raised |
| `test_alembic_upgrade` | `alembic upgrade head` on empty DB creates all tables with correct schema |
| `test_config_missing_required` | Starting app without `LINKEDIN_CLIENT_ID` raises `ValidationError` immediately |

All tests use an in-memory SQLite DB (`sqlite:///:memory:`) — no file system dependency, no cleanup needed.

---

## 3.11 Definition of Done — Sprint 3

A task is done when:

1. Code is written and passes all associated tests from Section 3.10
2. No `print()` statements — all output goes through `utils/logger`
3. All new functions and classes have type hints
4. All new public functions have docstrings (one-line minimum)
5. No raw SQL strings outside of `alembic/versions/` migration files
6. PR reviewed and merged to `main`
7. `uv run python cli.py sync` runs cleanly end-to-end on a real account after the change

---

*Document ends. Questions go to engineering before sprint kickoff.*

---

## Node.js Migration Status

The Node.js migration (`node-app/`) addresses several of the problems identified in this document, taking a different architectural approach from the Python optimization roadmap described above.

**Problem 1 (Duplicate Data):** The Node.js version currently uses `INSERT OR REPLACE`, the same approach as the Python codebase. However, the architecture supports easy migration to true `ON CONFLICT DO UPDATE` semantics via Drizzle ORM, which provides typed, composable query building with first-class upsert support.

**Problem 2 (No Type Safety):** The Node.js version uses TypeScript throughout the stack, providing compile-time type safety that catches errors before runtime. Zod validates configuration at startup (equivalent to the Pydantic BaseSettings approach proposed in Section 3.5). Drizzle ORM provides a fully typed database schema, eliminating the mismatch between application code and database structure.

**Problem 3 (Tech Stack Mismatch):** The Node.js version consolidates the server layer into a single Fastify server, replacing the Flask + FastAPI split. The frontend is a React SPA, replacing the inline HTML templates. Async operations use native `async/await` for concurrent API calls, which is idiomatic in Node.js without requiring a separate library like `httpx`.

**Key performance improvement:** The Node.js ingestion pipeline uses `Promise.all` combined with `p-limit(3)` for parallel batch processing of metrics, providing bounded concurrency with a semaphore pattern. This approach is estimated to be 3-4x faster than the current synchronous Python sync, which processes API calls sequentially.

**Real-time feedback:** SSE (Server-Sent Events) streaming provides real-time sync progress feedback to the frontend, allowing users to see each stage of the ingestion process as it happens.

**Note on the optimization roadmap:** The Phase 1 through Phase 4 optimization roadmap in this document was designed for the Python stack. The Node.js migration takes a fundamentally different approach -- rebuilding the stack from the ground up rather than incrementally modernizing -- but addresses the same underlying concerns: data deduplication, type safety, and architectural alignment with a modern SaaS product.