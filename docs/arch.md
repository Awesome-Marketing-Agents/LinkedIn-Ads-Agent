# LinkedIn Ads Action Center - Architecture Documentation

**Version:** 1.0  
**Last Updated:** February 19, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Module APIs and Data Flows](#module-apis-and-data-flows)
4. [LLM Integration Interfaces](#llm-integration-interfaces)
5. [Node/Brain Boundary](#nodebrain-boundary)
6. [Data Models](#data-models)
7. [Extension Points](#extension-points)

---

## Overview

The LinkedIn Ads Action Center is a modular system designed to:

- **Ingest** campaign data from LinkedIn Ads API
- **Store** data in a normalized SQLite database
- **Analyze** performance using an LLM-powered "brain"
- **Recommend** actionable optimizations
- **Execute** approved changes via API

The architecture separates concerns into **node modules** (data operations) and **brain modules** (LLM-powered analysis), creating a clear boundary for reasoning and action.

---

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACES                        │
├─────────────────────────────────────────────────────────────┤
│  • CLI (cli.py)                                             │
│  • Web Dashboard (main.py - Flask)                          │
│  • OAuth Callback Server (auth/callback.py - FastAPI)      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      CORE NODE MODULES                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │   auth/          │    │   ingestion/     │              │
│  │  - manager.py    │    │  - client.py     │              │
│  │  - callback.py   │    │  - fetchers.py   │              │
│  │                  │    │  - metrics.py    │              │
│  └──────────────────┘    └──────────────────┘              │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │   storage/       │    │   utils/         │              │
│  │  - database.py   │    │  - logger.py     │              │
│  │  - repository.py │    │  - errors.py     │              │
│  │  - snapshot.py   │    │                  │              │
│  └──────────────────┘    └──────────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  LLM BRAIN MODULES (Future)                 │
├─────────────────────────────────────────────────────────────┤
│  • analysis/     - Performance analysis                     │
│  • agent/        - LLM reasoning engine                     │
│  • models/       - Prompt templates and schemas             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                        │
├─────────────────────────────────────────────────────────────┤
│  • LinkedIn Ads API (ads-api.linkedin.com)                  │
│  • LLM Provider (OpenAI, Anthropic, etc.)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Module APIs and Data Flows

### 1. Authentication Module (`auth/`)

**Purpose:** Manage OAuth 2.0 tokens for LinkedIn API access.

#### API Surface

**`auth/manager.py` - `AuthManager`**

```python
class AuthManager:
    def get_authorization_url() -> str
        """Returns LinkedIn OAuth URL for user to visit."""
        
    def exchange_code_for_token(auth_code: str) -> dict
        """Exchanges authorization code for access/refresh tokens."""
        
    def refresh_access_token() -> dict
        """Uses refresh token to get new access token."""
        
    def get_access_token() -> str
        """Returns valid access token (auto-refreshes if expired)."""
        
    def is_authenticated() -> bool
        """Checks if valid token exists."""
        
    def token_status() -> dict
        """Returns token health summary."""
```

**Exceptions Raised:**
- `AuthenticationError` - OAuth failures, missing tokens
- `TokenExpiredError` - Token refresh required but failed

**Data Flow:**

```
User → OAuth URL → LinkedIn → Authorization Code → exchange_code_for_token()
    → Save tokens.json → get_access_token() → API Client
```

---

### 2. Ingestion Module (`ingestion/`)

**Purpose:** Fetch raw data from LinkedIn Ads API.

#### API Surface

**`ingestion/client.py` - `LinkedInClient`**

```python
class LinkedInClient:
    def __init__(auth: AuthManager)
        """Initialize with AuthManager for token handling."""
        
    def get(path: str, params_str: str = "") -> dict
        """GET request to LinkedIn API endpoint."""
        
    def get_all_pages(
        path: str,
        params_str: str = "",
        key: str = "elements",
        page_size: int = 100
    ) -> list[dict]
        """Fetch all pages using offset or token-based pagination."""
```

**Exceptions Raised:**
- `LinkedInAPIError` - HTTP errors (4xx, 5xx)
- `RateLimitError` - 429 rate limit exceeded

**`ingestion/fetchers.py`**

```python
def fetch_ad_accounts(client: LinkedInClient) -> list[dict]
    """GET /adAccounts?q=search"""
    
def fetch_campaigns(
    client: LinkedInClient,
    account_id: int,
    statuses: list[str] | None = None
) -> list[dict]
    """GET /adAccounts/{id}/adCampaigns?q=search"""
    
def fetch_creatives(
    client: LinkedInClient,
    account_id: int,
    campaign_ids: list[int] | None = None
) -> list[dict]
    """GET /adAccounts/{id}/creatives?q=criteria"""
```

**`ingestion/metrics.py`**

```python
def fetch_campaign_metrics(
    client: LinkedInClient,
    campaign_ids: list[int],
    start: datetime.date,
    end: datetime.date,
    granularity: str = "DAILY"
) -> list[dict]
    """GET /adAnalytics?pivot=CAMPAIGN"""
    
def fetch_creative_metrics(
    client: LinkedInClient,
    campaign_ids: list[int],
    start: datetime.date,
    end: datetime.date
) -> list[dict]
    """GET /adAnalytics?pivot=CREATIVE"""
    
def fetch_demographics(
    client: LinkedInClient,
    account_id: int,
    campaign_ids: list[int],
    start: datetime.date,
    end: datetime.date
) -> dict[str, list[dict]]
    """GET /adAnalytics with demographic pivots"""
```

**Data Flow:**

```
Client → fetchers.fetch_*() → LinkedInClient.get_all_pages()
    → HTTP Request → LinkedIn API → Raw JSON Response
```

---

### 3. Storage Module (`storage/`)

**Purpose:** Persist data in SQLite with normalized schema.

#### API Surface

**`storage/database.py`**

```python
def init_database(db_path: Path | None = None) -> Path
    """Initialize database schema."""
    
def get_connection(db_path: Path | None = None) -> sqlite3.Connection
    """Return connection with schema applied."""
```

**Schema Tables:**
- `ad_accounts`
- `campaigns`
- `creatives`
- `campaign_daily_metrics`
- `creative_daily_metrics`
- `audience_demographics`

**`storage/repository.py`**

```python
def persist_snapshot(snap: dict, db_path: Path | None = None) -> None
    """Upsert entire snapshot into database."""
    
def table_counts(db_path: Path | None = None) -> dict[str, int]
    """Return row counts for all tables."""
    
def active_campaign_audit(db_path: Path | None = None) -> list[dict]
    """Return active campaigns with potential issues."""
```

**Exceptions Raised:**
- `StorageError` - Database operation failures

**`storage/snapshot.py`**

```python
def assemble_snapshot(
    accounts: list[dict],
    campaigns_by_account: dict[int, list[dict]],
    creatives_by_account: dict[int, list[dict]],
    campaign_metrics: list[dict],
    creative_metrics: list[dict],
    demographics: dict[str, list[dict]],
    date_start: datetime.date,
    date_end: datetime.date
) -> dict
    """Transform API data into structured snapshot."""
    
def save_snapshot_to_disk(
    snapshot: dict,
    snapshot_dir: Path | None = None
) -> Path
    """Save snapshot as timestamped JSON file."""
```

**Data Flow:**

```
Raw API Data → assemble_snapshot() → Structured Dict
    ↓
persist_snapshot() → SQLite Database
    ↓
save_snapshot_to_disk() → snapshots/{timestamp}.json
```

---

### 4. Utilities Module (`utils/`)

**Purpose:** Cross-cutting concerns (logging, errors).

#### API Surface

**`utils/logger.py`**

```python
logger: logging.Logger
    """Singleton logger instance for linkedin_action_center."""
    
def get_logger() -> logging.Logger
    """Returns the singleton logger."""
    
def log_api_call(method: str, endpoint: str, status: int, duration: float)
    """Convenience function for API call logging."""
    
def log_auth_event(event: str, details: str)
    """Log authentication events."""
    
def log_sync_progress(resource: str, current: int, total: int)
    """Log sync progress."""
    
def log_error(message: str, context: dict | None = None)
    """Log errors with context."""
```

**Features:**
- Console output with `rich.RichHandler`
- File output to `logs/linkedin_action_center.log`
- Automatic exception formatting with `rich.traceback`

**`utils/errors.py`**

```python
# Base exception
class LinkedInActionCenterError(Exception)
    def display() -> None  # Rich-formatted error display

# Domain-specific exceptions
class AuthenticationError(LinkedInActionCenterError)
class TokenExpiredError(AuthenticationError)
class LinkedInAPIError(LinkedInActionCenterError)
class RateLimitError(LinkedInAPIError)
class ValidationError(LinkedInActionCenterError)
class ConfigurationError(LinkedInActionCenterError)
class StorageError(LinkedInActionCenterError)
class DataFetchError(LinkedInActionCenterError)

def handle_error(error: Exception, show_traceback: bool = False)
    """Display error with rich formatting."""
```

---

### 5. Core Module (`core/`)

**Purpose:** Configuration and constants.

#### API Surface

**`core/config.py`**

Environment-based configuration loaded from `.env`:

```python
# LinkedIn API
LINKEDIN_CLIENT_ID: str
LINKEDIN_CLIENT_SECRET: str
LINKEDIN_REDIRECT_URI: str

# Files
TOKENS_FILE: Path = Path("tokens.json")
DATABASE_FILE: Path = Path("linkedin_ads.db")
SNAPSHOT_DIR: Path = Path("snapshots")

# OAuth
OAUTH_STATE: str = "random_state_string"
```

**`core/constants.py`**

LinkedIn API constants:

```python
API_BASE_URL: str = "https://api.linkedin.com/rest"
OAUTH2_BASE_URL: str = "https://www.linkedin.com/oauth/v2"
INTROSPECT_URL: str = "https://www.linkedin.com/oauth/v2/introspectToken"
LINKEDIN_API_VERSION: str = "202402"

SCOPES: list[str] = [
    "r_ads",
    "r_ads_reporting",
    "rw_ads",
    "r_organization_admin"
]
```

---

## Data Flow: Complete Sync Process

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User initiates sync (CLI or Web)                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. auth.manager.get_access_token()                             │
│    - Validates token expiry                                     │
│    - Auto-refreshes if needed                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. ingestion/fetchers fetch raw data                           │
│    a) fetch_ad_accounts(client)                                 │
│    b) For each account:                                         │
│       - fetch_campaigns(client, account_id)                     │
│       - fetch_creatives(client, account_id, campaign_ids)       │
│    c) fetch_campaign_metrics(client, campaign_ids, dates)       │
│    d) fetch_creative_metrics(client, campaign_ids, dates)       │
│    e) fetch_demographics(client, account_id, campaign_ids)      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. storage/snapshot.assemble_snapshot()                         │
│    - Transforms raw API dicts into structured format            │
│    - Aggregates metrics                                         │
│    - Computes derived KPIs (CTR, CPC, etc.)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Parallel persistence:                                        │
│    a) storage/repository.persist_snapshot(snapshot)             │
│       → SQLite database (upsert)                                │
│    b) storage/snapshot.save_snapshot_to_disk(snapshot)          │
│       → snapshots/{timestamp}.json                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. Return status to user interface                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## LLM Integration Interfaces

### Design Principles

The LLM "brain" integration follows these principles:

1. **Stateless Analysis** - Brain receives snapshot, returns recommendations
2. **Structured I/O** - JSON schemas for requests/responses
3. **Action Separation** - Brain suggests, Node executes
4. **Audit Trail** - All recommendations and actions logged

### Brain Input Interface

**Snapshot Schema** (input to LLM):

```python
{
    "date_range": {
        "start": "2026-02-12",
        "end": "2026-02-19"
    },
    "accounts": [
        {
            "id": 123456,
            "name": "Acme Corp",
            "status": "ACTIVE",
            "currency": "USD",
            "total_metrics": {
                "impressions": 50000,
                "clicks": 1250,
                "spend": 2500.00,
                "conversions": 45,
                "ctr": 2.5,
                "cpc": 2.00,
                "cvr": 3.6
            },
            "campaigns": [
                {
                    "id": 789012,
                    "name": "Q1 Lead Gen",
                    "status": "ACTIVE",
                    "type": "SPONSORED_INMAILS",
                    "settings": {
                        "daily_budget": 100.00,
                        "bid_strategy": "MAXIMUM_BID",
                        "creative_selection": "OPTIMIZED",
                        "offsite_delivery_enabled": true,
                        "audience_expansion_enabled": false
                    },
                    "weekly_metrics": { ... },
                    "daily_metrics": [ ... ],
                    "creatives": [ ... ]
                }
            ]
        }
    ]
}
```

### Brain Output Interface

**Recommendation Schema** (output from LLM):

```python
{
    "analyzed_at": "2026-02-19T21:30:00Z",
    "analysis_model": "gpt-4o",
    "summary": "3 high-priority optimizations identified",
    "recommendations": [
        {
            "id": "rec_001",
            "priority": "HIGH",
            "confidence": 0.92,
            "category": "BUDGET_OPTIMIZATION",
            "title": "Increase budget for high-performing campaign",
            "rationale": "Campaign 789012 has CTR 150% above account average...",
            "metrics_evidence": {
                "current_ctr": 3.75,
                "account_avg_ctr": 2.5,
                "current_cvr": 5.2,
                "account_avg_cvr": 3.6
            },
            "suggested_action": {
                "type": "UPDATE_CAMPAIGN_BUDGET",
                "campaign_id": 789012,
                "parameters": {
                    "daily_budget": 150.00,
                    "increase_pct": 50
                },
                "expected_impact": {
                    "additional_conversions": 15,
                    "estimated_cost": 750.00,
                    "estimated_roi": 2.3
                }
            },
            "urgency": "Implement within 24 hours",
            "risks": ["Monitor CPC increase", "Watch conversion volume"]
        }
    ],
    "insights": [
        {
            "type": "TREND",
            "message": "Overall account CTR declining 12% week-over-week"
        }
    ]
}
```

### Integration Points

**Module: `analysis/` (Future)**

```python
def analyze_snapshot(
    snapshot: dict,
    llm_provider: str = "openai",
    model: str = "gpt-4o"
) -> dict:
    """
    Send snapshot to LLM for analysis.
    
    Returns recommendation schema.
    """
    pass
```

**Module: `agent/` (Future)**

```python
def execute_recommendation(
    rec: dict,
    client: LinkedInClient,
    dry_run: bool = True
) -> dict:
    """
    Execute a recommended action via LinkedIn API.
    
    Returns execution result with before/after state.
    """
    pass

def approve_recommendation(rec_id: str, user: str) -> None:
    """
    Mark recommendation as approved for execution.
    
    Logs approval in audit trail.
    """
    pass
```

---

## Node/Brain Boundary

### Clear Separation of Concerns

The architecture enforces a strict boundary between:

**NODE (Data Operations)**
- Authenticate with LinkedIn
- Fetch data from APIs
- Transform and normalize data
- Persist to database
- Serve data to interfaces

**BRAIN (LLM-Powered Analysis)**
- Analyze campaign performance
- Identify optimization opportunities
- Generate actionable recommendations
- Explain reasoning and evidence
- Predict impact of changes

### Boundary Guarantees

1. **Brain Never Accesses APIs Directly**
   - Brain receives only processed snapshots
   - No raw API credentials in brain context
   - All data transformations happen in node layer

2. **Node Never Makes Strategic Decisions**
   - Node executes explicit instructions
   - No heuristics or optimization logic in node
   - All "intelligence" lives in brain layer

3. **Explicit Action Approval**
   - Brain recommends, user approves, node executes
   - Audit trail for all recommendations and actions
   - No automatic execution without approval

### Interface Contract

```python
# Node provides to Brain
class SnapshotInterface(TypedDict):
    """Structured campaign data for analysis"""
    date_range: dict
    accounts: list[dict]
    # ... see Brain Input Interface section

# Brain provides to Node
class RecommendationInterface(TypedDict):
    """Actionable recommendations with evidence"""
    analyzed_at: str
    recommendations: list[dict]
    insights: list[dict]
    # ... see Brain Output Interface section

# Node executes from Brain
class ActionInterface(TypedDict):
    """Executable action for LinkedIn API"""
    type: str  # UPDATE_CAMPAIGN_BUDGET, PAUSE_CREATIVE, etc.
    campaign_id: int
    parameters: dict
    # ... validated before execution
```

### Communication Flow

```
┌──────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│  "Analyze my campaigns and suggest optimizations"       │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│                   NODE LAYER (Python)                    │
│  1. Fetch latest data from LinkedIn                     │
│  2. Assemble structured snapshot                         │
│  3. Serialize snapshot to JSON                           │
└──────────────────────────────────────────────────────────┘
                        ↓ (JSON)
┌──────────────────────────────────────────────────────────┐
│                  BRAIN LAYER (LLM)                       │
│  1. Parse snapshot structure                             │
│  2. Analyze metrics and trends                           │
│  3. Generate recommendations with evidence               │
│  4. Serialize recommendations to JSON                    │
└──────────────────────────────────────────────────────────┘
                        ↓ (JSON)
┌──────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│  "Here are 3 recommendations: [display]"                 │
│  "Approve recommendation #1?"                            │
└──────────────────────────────────────────────────────────┘
                        ↓ (if approved)
┌──────────────────────────────────────────────────────────┐
│                   NODE LAYER (Python)                    │
│  1. Validate action parameters                           │
│  2. Execute via LinkedIn API                             │
│  3. Log action and result                                │
│  4. Confirm to user                                      │
└──────────────────────────────────────────────────────────┘
```

---

## Data Models

### Campaign Snapshot Structure

**When assembled by `storage/snapshot.assemble_snapshot()`:**

```python
{
    "date_range": {
        "start": "2026-02-12",
        "end": "2026-02-19",
        "days": 7
    },
    "fetched_at": "2026-02-19T21:15:28Z",
    "accounts": [
        {
            "id": 123456,
            "name": "Acme Corp",
            "status": "ACTIVE",
            "currency": "USD",
            "type": "BUSINESS",
            "test": false,
            
            # Aggregated metrics across all campaigns
            "total_metrics": {
                "impressions": 50000,
                "clicks": 1250,
                "spend": 2500.00,
                "landing_page_clicks": 980,
                "conversions": 45,
                "likes": 120,
                "comments": 35,
                "shares": 28,
                "follows": 15,
                "leads": 32,
                # Derived ratios
                "ctr": 2.5,
                "cpc": 2.00,
                "cpl": 78.13,
                "cvr": 3.6
            },
            
            # Trend metrics (current vs previous period)
            "weekly_metrics": {
                "current": { ... },
                "previous": { ... },
                "change_pct": {
                    "impressions": -5.2,
                    "clicks": 3.1,
                    "spend": -2.8
                }
            },
            
            "campaigns": [
                {
                    "id": 789012,
                    "name": "Q1 Lead Gen",
                    "status": "ACTIVE",
                    "type": "SPONSORED_INMAILS",
                    
                    "settings": {
                        "daily_budget": 100.00,
                        "total_budget": null,
                        "bid_strategy": "MAXIMUM_BID",
                        "unit_cost": 5.00,
                        "creative_selection": "OPTIMIZED",
                        "offsite_delivery_enabled": true,
                        "audience_expansion_enabled": false
                    },
                    
                    "metrics": { ... },  # Aggregated for campaign
                    "weekly_metrics": { ... },
                    
                    # Daily time series
                    "daily_metrics": [
                        {
                            "date": "2026-02-12",
                            "impressions": 7142,
                            "clicks": 178,
                            "spend": 356.00,
                            "conversions": 6
                        },
                        # ... 7 days
                    ],
                    
                    "creatives": [
                        {
                            "id": "creative_456",
                            "status": "ACTIVE",
                            "metrics": { ... },
                            "daily_metrics": [ ... ]
                        }
                    ]
                }
            ],
            
            # Demographic breakdowns
            "demographics": {
                "MEMBER_JOB_TITLE": [
                    {
                        "segment": "Engineer",
                        "impressions": 8500,
                        "clicks": 255,
                        "spend": 510.00,
                        "ctr": 3.0
                    }
                ],
                # ... other pivots
            }
        }
    ]
}
```

---

## Extension Points

### Adding New Data Sources

To add a new LinkedIn entity (e.g., lead forms):

1. **Add fetcher** in `ingestion/fetchers.py`:
   ```python
   def fetch_lead_forms(client: LinkedInClient, account_id: int) -> list[dict]:
       return client.get_all_pages(f"/adAccounts/{account_id}/leadForms")
   ```

2. **Extend database schema** in `storage/database.py`:
   ```sql
   CREATE TABLE IF NOT EXISTS lead_forms (
       id TEXT PRIMARY KEY,
       account_id INTEGER,
       name TEXT,
       ...
   )
   ```

3. **Add upsert logic** in `storage/repository.py`:
   ```python
   def _upsert_lead_forms(cur, account_id, forms, now): ...
   ```

4. **Include in snapshot** in `storage/snapshot.py`:
   ```python
   account_dict["lead_forms"] = [{"id": f["id"], ...} for f in forms]
   ```

### Adding New LLM Providers

To support a new LLM provider:

1. **Create provider adapter** in `agent/providers/`:
   ```python
   class AnthropicProvider(BaseLLMProvider):
       def analyze(self, snapshot: dict) -> dict:
           # Format snapshot for Claude API
           # Call Anthropic API
           # Parse response into recommendation schema
   ```

2. **Register in config** `core/config.py`:
   ```python
   LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
   LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
   ```

3. **Update analysis dispatcher** in `analysis/`:
   ```python
   def analyze_snapshot(snapshot, provider="openai"):
       if provider == "anthropic":
           return AnthropicProvider().analyze(snapshot)
   ```

### Adding New Action Types

To add a new executable action (e.g., create new campaign):

1. **Define action schema** in `agent/actions.py`:
   ```python
   class CreateCampaignAction(TypedDict):
       type: Literal["CREATE_CAMPAIGN"]
       account_id: int
       name: str
       budget: float
       targeting: dict
   ```

2. **Implement executor** in `agent/executors.py`:
   ```python
   def execute_create_campaign(action: CreateCampaignAction, client: LinkedInClient):
       payload = _build_campaign_payload(action)
       response = client.post("/campaigns", payload)
       return {"campaign_id": response["id"], "status": "created"}
   ```

3. **Add to dispatcher** in `agent/executor.py`:
   ```python
   ACTION_EXECUTORS = {
       "CREATE_CAMPAIGN": execute_create_campaign,
       # ...
   }
   ```

---

## Testing Strategy

### Unit Tests

- **Location:** `tests/`
- **Coverage:** 69 tests across 5 test files
- **Command:** `uv run pytest tests/ -v`

**Test Organization:**
- `test_auth_manager.py` - OAuth flow, token management (15 tests)
- `test_client.py` - HTTP client, pagination, error handling (12 tests)
- `test_errors.py` - Custom exceptions (13 tests)
- `test_logger.py` - Logging functionality (15 tests)
- `test_repository.py` - Database operations (14 tests)

### Integration Testing (Future)

- End-to-end sync process
- LLM recommendation generation
- Action execution with mocked APIs

### Test Fixtures

**`tests/conftest.py`** provides:
- `mock_tokens` - Valid token dict
- `mock_auth_manager` - AuthManager with tokens
- `mock_response` - HTTP response objects
- `temp_db` - Temporary test database

---

## Logging and Monitoring

### Log Levels

- **INFO:** Normal operations (sync complete, API calls)
- **WARNING:** Degraded performance (rate limits approaching)
- **ERROR:** Operation failures (API errors, auth failures)

### Log Output

- **Console:** Rich-formatted with colors and timestamps
- **File:** `logs/linkedin_action_center.log` (plain text)

### Key Logging Points

```python
log_auth_event("Token refresh", "Successfully refreshed access token")
log_api_call("GET", "/campaigns", 200, 0.45)
log_sync_progress("campaigns", 5, 10)
log_error("Database persistence failed", context={"snapshot_size": 12345})
```

---

## Error Handling Strategy

### Exception Hierarchy

```
LinkedInActionCenterError (base)
├── AuthenticationError
│   └── TokenExpiredError
├── LinkedInAPIError
│   └── RateLimitError
├── ValidationError
├── ConfigurationError
├── StorageError
└── DataFetchError
```

### Error Propagation

1. **API Layer:** Catch HTTP errors → Raise domain exceptions
2. **Service Layer:** Catch domain exceptions → Log → Re-raise
3. **Interface Layer:** Catch all exceptions → Display to user

### Rich Error Display

All custom exceptions support:
```python
try:
    client.get("/campaigns")
except LinkedInAPIError as e:
    e.display()  # Rich-formatted output to console
```

---

## Configuration Management

### Environment Variables

**Required:**
- `LINKEDIN_CLIENT_ID`
- `LINKEDIN_CLIENT_SECRET`
- `LINKEDIN_REDIRECT_URI`

**Optional:**
- `DATABASE_FILE` (default: `linkedin_ads.db`)
- `SNAPSHOT_DIR` (default: `snapshots/`)
- `LOG_LEVEL` (default: `INFO`)

### Config File

Create `.env` in project root:

```bash
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_secret
LINKEDIN_REDIRECT_URI=http://localhost:8080/callback
```

---

## Deployment Considerations

### Production Checklist

- [ ] Store `.env` securely (not in version control)
- [ ] Use production database path (not in-memory SQLite)
- [ ] Configure log rotation for `logs/linkedin_action_center.log`
- [ ] Set up monitoring for rate limit warnings
- [ ] Implement backup strategy for `tokens.json`
- [ ] Schedule periodic token refresh
- [ ] Configure HTTPS for OAuth callback (not `http://localhost`)

### Security Best Practices

1. **Token Storage:** Encrypt `tokens.json` at rest
2. **Database:** SQLite with WAL mode (already configured)
3. **API Keys:** Never log client secrets
4. **OAuth State:** Use cryptographically secure random state
5. **LLM Context:** Sanitize PII before sending to LLM

---

## Future Architecture Enhancements

### Phase 1: LLM Integration (Current Sprint)

- [ ] Implement `analysis/analyzer.py` with OpenAI integration
- [ ] Create prompt templates in `agent/prompts/`
- [ ] Build recommendation approval UI in web dashboard
- [ ] Add action execution engine

### Phase 2: Advanced Features

- [ ] Multi-user support with role-based access
- [ ] Scheduled analysis and alerts
- [ ] Webhook integration for real-time optimization
- [ ] A/B test tracking and analysis

### Phase 3: Scale & Performance

- [ ] Replace SQLite with PostgreSQL for multi-user
- [ ] Implement Redis caching for API responses
- [ ] Add background job queue (Celery) for async processing
- [ ] Horizontal scaling for web interface

---

## Appendix: Quick Reference

### Key Files

| File | Purpose |
|------|---------|
| `cli.py` | Command-line interface entry point |
| `main.py` | Flask web dashboard |
| `auth/manager.py` | OAuth token management |
| `auth/callback.py` | FastAPI OAuth callback server |
| `ingestion/client.py` | HTTP client for LinkedIn API |
| `ingestion/fetchers.py` | Data fetching functions |
| `ingestion/metrics.py` | Analytics fetching |
| `storage/database.py` | SQLite schema |
| `storage/repository.py` | Database persistence |
| `storage/snapshot.py` | Snapshot assembly |
| `utils/logger.py` | Logging configuration |
| `utils/errors.py` | Custom exceptions |

### Common Commands

```bash
# Install dependencies
uv sync

# Run CLI
uv run python cli.py status
uv run python cli.py auth
uv run python cli.py sync

# Run web dashboard
uv run python main.py

# Run tests
uv run pytest tests/ -v

# Check logs
cat logs/linkedin_action_center.log
```

---

**End of Architecture Documentation**
