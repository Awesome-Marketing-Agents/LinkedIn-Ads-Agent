# Data Ingestion Best Practices
### A Python-Specific Reference for Third-Party REST API Pipelines

**Audience:** Intermediate Python developer  
**Stack:** Python 3.12+ · asyncio · httpx · Pydantic · SQLModel · FastAPI  
**Scope:** Third-party REST API ingestion (e.g. LinkedIn Ads API)  
**Updated:** February 2026

---

## How to Read This Document

This is a reference guide, not a tutorial. Each section covers one concept: what it is, why it matters, when to use it, and how it works — with annotated pseudocode diagrams. You do not need to implement everything at once. Treat this as a menu of patterns you reach for when problems arise.

**Concept Map — How everything connects:**

```
REST API Source
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  TRANSPORT LAYER                                        │
│  httpx AsyncClient · Connection Pooling · HTTP/2        │
│  Timeouts · Retry + Backoff · Circuit Breaker           │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  CONTROL LAYER                                          │
│  Rate Limiting (Token Bucket) · Semaphores              │
│  Batch Processing · Pagination · Concurrency            │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  EFFICIENCY LAYER                                       │
│  Incremental Ingestion · High-Water Mark                │
│  Freshness Gate · Caching                               │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  DATA QUALITY LAYER                                     │
│  Pydantic Validation · Schema Evolution                 │
│  Dead Letter Queue · Idempotency                        │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  STORAGE LAYER                                          │
│  True Upsert · Raw Store (S3) · Write Strategies        │
│  Transaction Management                                 │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  OBSERVABILITY LAYER                                    │
│  Structured Logging · Metrics · Run Tracking            │
│  Data Lineage · Alerting                                │
└─────────────────────────────────────────────────────────┘
```

---

## Section 1 — Transport Layer

### 1.1 Async vs. Sync: Why It Matters for API Ingestion

When you call an API with the synchronous `requests` library, your program **stops and waits** for the response before doing anything else. One call takes 200ms → your program sits idle for 200ms. Call 50 APIs in sequence → you wait 10 seconds total.

With `asyncio` + `httpx`, your program **fires a request and immediately moves on** to start the next one. All 50 requests are in-flight simultaneously. You wait for the slowest one — roughly 200ms total instead of 10 seconds.

```
SYNC (requests):
──────────────────────────────────────────────────────────►
[call 1 ──wait──] [call 2 ──wait──] [call 3 ──wait──]
Total time = sum of all calls (e.g. 10s)

ASYNC (asyncio + httpx):
──────────────────────────────────────────────────────────►
[call 1 ──wait──]
    [call 2 ──wait──]
        [call 3 ──wait──]
Total time ≈ slowest single call (e.g. 0.2s)
```

**When async is the right tool:**
- Multiple independent API calls (campaigns + creatives + metrics can all be in-flight together)
- Network I/O is the bottleneck — not CPU computation
- You need to run pipelines for many accounts without queuing them serially

**When sync is fine:**
- Single sequential calls where order matters
- Simple scripts or one-off data pulls
- Your team is not yet familiar with async patterns — async bugs are harder to debug

---

### 1.2 httpx AsyncClient — The Right Way to Use It

`httpx` is the modern Python HTTP client. It supports async natively and is designed around one central principle: **create the client once, reuse it everywhere**.

```
WRONG — recreates client on every call (no connection reuse):
─────────────────────────────────────────────────────────────
async def fetch_campaigns(account_id):
    async with httpx.AsyncClient() as client:   # ← new client = new TCP handshake
        return await client.get(f"/campaigns/{account_id}")

# Called 100 times → 100 separate TCP handshakes. Slow.

─────────────────────────────────────────────────────────────
CORRECT — single shared client, connections reused:
─────────────────────────────────────────────────────────────
# Created once at app startup
client = httpx.AsyncClient(
    base_url   = "https://api.linkedin.com/rest",
    timeout    = httpx.Timeout(connect=3.0, read=10.0, write=5.0),
    limits     = httpx.Limits(max_connections=20, max_keepalive_connections=10),
    headers    = {"LinkedIn-Version": "202602"}
)

# Passed into every function that needs it
async def fetch_campaigns(client, account_id):
    return await client.get(f"/adCampaigns", params={"account": account_id})

# Called 100 times → reuses existing connections. Fast.
```

**Connection pooling in plain terms:** TCP connections are expensive to create (the "handshake" takes several round trips). A connection pool keeps connections alive and reuses them. httpx manages this automatically when you use one persistent `AsyncClient`.

**Timeout configuration — set ALL four:**

```
httpx.Timeout(
    connect = 3.0,   # how long to wait to establish a connection
    read    = 10.0,  # how long to wait for data to start arriving
    write   = 5.0,   # how long to wait to send request data
    pool    = 3.0    # how long to wait for a connection from the pool
)

Why all four? A missing connect timeout means your pipeline can hang
indefinitely if LinkedIn's server is unreachable.
A missing read timeout means it hangs if the server accepts the connection
but never responds.
"Timeout" by itself sets all four to the same value — usually too blunt.
```

---

### 1.3 Retry with Exponential Backoff + Jitter

**What it is:** When an API call fails due to a temporary problem (network blip, server overload, 429 rate limit), you wait a moment and try again. "Exponential backoff" means you wait progressively longer on each retry. "Jitter" adds randomness to prevent many clients all retrying at the same time.

**Why jitter matters:** Imagine 50 clients all hit a 429 at the same time. Without jitter, all 50 retry after exactly 2 seconds — creating another simultaneous spike. With jitter, they retry at 2.1s, 1.8s, 2.4s, etc. — spreading the load.

```
Retry timeline with exponential backoff + jitter:

Attempt 1  ──► FAIL (429)
Wait: base=1s × 2^0 + random(0, 0.5) = ~1.3s
Attempt 2  ──► FAIL (429)
Wait: base=1s × 2^1 + random(0, 0.5) = ~2.4s
Attempt 3  ──► FAIL (500)
Wait: base=1s × 2^2 + random(0, 0.5) = ~4.2s
Attempt 4  ──► SUCCESS ✓

Formula: wait = min(cap, base * 2^attempt) + random(0, jitter)
Cap prevents waiting forever (e.g. max 60s)
```

**What to retry vs. what not to retry:**

```
RETRY (temporary problems):
  429  Too Many Requests     → wait and try again
  500  Internal Server Error → server hiccup, retry
  502  Bad Gateway           → transient network issue
  503  Service Unavailable   → server temporarily down
  504  Gateway Timeout       → request timed out in transit

DO NOT RETRY (permanent problems):
  400  Bad Request           → your request is malformed, fix it
  401  Unauthorized          → token is wrong or expired, re-auth first
  403  Forbidden             → you don't have permission, won't change
  404  Not Found             → the resource doesn't exist
  422  Unprocessable Entity  → validation failed on server side
```

**Python implementation with `tenacity`:**

```python
# tenacity is the standard Python library for retry logic
# pip install tenacity

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception,
    before_sleep_log,
)

def is_retryable(exception) -> bool:
    """Only retry on transient HTTP errors — not on 4xx client errors."""
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in {429, 500, 502, 503, 504}
    if isinstance(exception, (httpx.ConnectTimeout, httpx.ReadTimeout)):
        return True
    return False

@retry(
    stop=stop_after_attempt(4),           # max 4 attempts total
    wait=wait_exponential_jitter(         # 1s → 2s → 4s + jitter
        initial=1, max=30, jitter=0.5
    ),
    retry=retry_if_exception(is_retryable),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True                          # after max attempts, raise original error
)
async def fetch_with_retry(client, path, params):
    response = await client.get(path, params=params)
    response.raise_for_status()
    return response.json()
```

---

### 1.4 Circuit Breaker

**The problem retry alone doesn't solve:** Imagine LinkedIn's API goes down completely for 30 minutes. Without a circuit breaker, every request retries 4 times with backoff — meaning hundreds of retry chains all hammering a dead endpoint. Your pipeline stalls, burns time, and returns no data.

**What a circuit breaker does:** It's a switch that "trips" after a threshold of consecutive failures. Once tripped (open state), all calls immediately fail without hitting the API — fail fast. After a timeout, it enters "half-open" state and allows one test call. If it succeeds, the circuit closes and normal operation resumes.

```
Circuit Breaker State Machine:

         too many failures
CLOSED ──────────────────► OPEN
  ▲                          │
  │         timeout          │
  │◄────────────────────────►│
  │                       HALF-OPEN
  │                          │
  │   test call succeeds     │
  └──────────────────────────┘
  
         test call fails → back to OPEN

CLOSED:    Normal operation. Every call goes through.
OPEN:      Fail immediately. Don't even try the API.
           Returns cached/default value instead.
HALF-OPEN: One test call allowed. Decides whether to
           close or re-open.
```

**Key insight: circuit breaker wraps retry, not the other way around.**

```
WRONG layering:
  retry(circuit_breaker(api_call))
  → retries AFTER breaker opens → wastes time retrying a known-dead endpoint

CORRECT layering:
  circuit_breaker(retry(api_call))
  → breaker catches repeated retry failures as a single logical failure
  → once breaker opens, fails immediately without retrying
```

**Python implementation with `pybreaker`:**

```python
# pip install pybreaker

import pybreaker

# One breaker per integration point — not one global breaker
linkedin_breaker = pybreaker.CircuitBreaker(
    fail_max=5,           # open after 5 consecutive failures
    reset_timeout=60,     # try half-open after 60 seconds
    name="linkedin_ads_api"
)

# Wrap your API call
@linkedin_breaker
async def call_linkedin_api(client, path, params):
    response = await client.get(path, params=params)
    response.raise_for_status()
    return response.json()

# In your caller:
try:
    data = await call_linkedin_api(client, "/adAnalytics", params)
except pybreaker.CircuitBreakerError:
    # Breaker is open — serve from cache or skip this account
    logger.warning("LinkedIn API circuit open — using cached data")
    data = get_cached_data(account_id)
```

---

## Section 2 — Control Layer

### 2.1 Rate Limiting with Token Bucket

**The problem:** LinkedIn's API has rate limits. If you exceed them, you get a 429 and potentially a temporary ban. The naive approach is to just handle 429s when they come — but that's reactive. You've already wasted a request and need to wait. The better approach is proactive: self-impose a rate limit that stays under LinkedIn's limit.

**Token Bucket algorithm — the mental model:**

```
Imagine a bucket that holds tokens (permissions to make a request).

START:        [●●●●●●●●●●] 10 tokens full
Every second: +2 tokens added (refill rate), up to max capacity

Make a request → consume 1 token:
After 5 requests: [●●●●●     ] 5 tokens left

If bucket is empty:
[          ] 0 tokens → WAIT until refilled before sending request

Key properties:
- Allows bursts up to bucket capacity
- Long-term average rate is bounded by refill rate
- Never exceeds the cap — proactive, not reactive
```

**Why Token Bucket over fixed-window rate limiting:**

```
FIXED WINDOW (bad for burst APIs):
Window 1 (0-60s):  [●●●●●●●●●●] 10 requests used ✓
Window 2 (60-120s):[          ] 0 used yet
                              ↑
                   All 10 requests at second 59 + all 10 at second 60
                   = 20 requests in 2 seconds → rate limit violation!
                   Fixed window doesn't prevent cross-boundary bursts.

TOKEN BUCKET (handles this correctly):
Bucket refills at 10 tokens/minute = 1 token every 6 seconds
Burst of 10 at second 59 → empties bucket
Burst attempt at second 60 → bucket has 0.16 tokens → WAIT
Prevents the cross-boundary spike automatically.
```

**Per-account token bucket — critical for multi-tenant:**

```python
# One bucket per LinkedIn ad account
# If account A gets rate limited, account B is unaffected

from aiolimiter import AsyncLimiter  # pip install aiolimiter

class PerAccountRateLimiter:
    def __init__(self, rate: float = 10, period: float = 1.0):
        """
        rate:   max requests per period
        period: time window in seconds
        Example: rate=10, period=1.0 → max 10 requests/second per account
        """
        self._limiters: dict[str, AsyncLimiter] = {}
        self._rate   = rate
        self._period = period

    def get_limiter(self, account_id: str) -> AsyncLimiter:
        if account_id not in self._limiters:
            self._limiters[account_id] = AsyncLimiter(
                max_rate=self._rate,
                time_period=self._period
            )
        return self._limiters[account_id]

    async def acquire(self, account_id: str):
        async with self.get_limiter(account_id):
            pass  # blocks until a token is available

# Usage pattern:
rate_limiter = PerAccountRateLimiter(rate=10, period=1.0)

async def fetch_with_rate_limit(client, account_id, path, params):
    await rate_limiter.acquire(account_id)   # wait for token
    return await client.get(path, params=params)  # then call
```

**Adaptive rate limiting — responding to 429s:**

```
When you get a 429, LinkedIn often includes Retry-After: 30 in the header.
Use this to dynamically reduce your token bucket's refill rate:

On 429 received:
  1. Read Retry-After header (e.g. 30 seconds)
  2. Pause that account's bucket for 30 seconds
  3. After pause, resume at 50% of previous rate
  4. Gradually increase rate if no further 429s over next 5 minutes

This is "adaptive throttling" — more sophisticated than fixed rates.
```

---

### 2.2 Concurrency Control with Semaphores

**The problem:** `asyncio.gather()` with no limits will fire ALL tasks simultaneously. For 100 accounts, that's 100 concurrent API connections at once — a DDoS against LinkedIn from your own pipeline.

**A semaphore** is a counter that limits how many tasks can run at the same time.

```
Semaphore(value=5) means: max 5 tasks run simultaneously

Tasks waiting:   [T6] [T7] [T8] [T9] [T10]
Tasks running:   [T1] [T2] [T3] [T4] [T5]
                  ↑                    ↑
              When T1 finishes,    counter decrements
              T6 is allowed in     when T1 enters
              counter increments   the block

asyncio.gather() with Semaphore:
──────────────────────────────────────────────────────
Fires all coroutines, but only 5 run concurrently.
When one finishes, the next waiting one starts.
No task is starved. No server is flooded.
```

**Two semaphore scopes you need:**

```python
# Scope 1: Global — max concurrent accounts
GLOBAL_ACCOUNT_SEMAPHORE = asyncio.Semaphore(10)  # 10 accounts at once

# Scope 2: Per-account — max concurrent fetches per account
# (campaigns + creatives + metrics can run in parallel within one account,
#  but don't fire unlimited calls per account)

async def sync_account(account_id: str):
    # Global semaphore: limits total concurrent accounts
    async with GLOBAL_ACCOUNT_SEMAPHORE:
        per_account_sem = asyncio.Semaphore(5)  # 5 concurrent fetches per account

        async def fetch_with_sem(coro):
            async with per_account_sem:
                return await coro

        # These 3 fetches run concurrently, but bounded by per_account_sem
        campaigns, creatives, metrics = await asyncio.gather(
            fetch_with_sem(fetch_campaigns(account_id)),
            fetch_with_sem(fetch_creatives(account_id)),
            fetch_with_sem(fetch_metrics(account_id)),
        )
```

---

### 2.3 Batch Processing

**What it is:** Instead of calling an API once per item (one API call per campaign), you group items together and call the API once for the group. Some APIs support this; LinkedIn's `adAnalytics` endpoint lets you pass up to 20 campaign IDs per request.

```
WITHOUT batching (1 call per campaign):
  GET /adAnalytics?campaigns=List(camp_1)   → 1 API call
  GET /adAnalytics?campaigns=List(camp_2)   → 1 API call
  ...
  GET /adAnalytics?campaigns=List(camp_50)  → 1 API call
  Total: 50 API calls

WITH batching (20 campaigns per call):
  GET /adAnalytics?campaigns=List(camp_1,...,camp_20)  → 1 API call
  GET /adAnalytics?campaigns=List(camp_21,...,camp_40) → 1 API call
  GET /adAnalytics?campaigns=List(camp_41,...,camp_50) → 1 API call
  Total: 3 API calls — 94% reduction
```

**Batch size tradeoffs:**

```
Too small → too many API calls → rate limits hit sooner
Too large → URL length exceeded → 414 errors (LinkedIn's limit is ~20 IDs)
            Also: one bad ID in a large batch can fail the whole batch

LinkedIn-specific: batch size of 20 campaign IDs is the safe sweet spot.
Use 10 if you're hitting 414 errors.

Pseudocode for batching:
─────────────────────────────────────────────────────────
def batch(items: list, size: int) -> list[list]:
    """Split a list into chunks of `size`."""
    return [items[i:i+size] for i in range(0, len(items), size)]

campaign_batches = batch(all_campaign_ids, size=20)
tasks = [fetch_metrics(client, batch) for batch in campaign_batches]
results = await asyncio.gather(*tasks)  # all batches in parallel
flat_results = [item for batch in results for item in batch]
```

---

### 2.4 Pagination

**The problem:** APIs don't return all data in one response. They return a page of results with a pointer to the next page. If you only read page 1, you silently miss data.

```
LinkedIn pagination models:

Model A — Offset-based (most LinkedIn endpoints):
  GET /adCampaigns?start=0&count=100   → returns elements [0..99], total=350
  GET /adCampaigns?start=100&count=100 → returns elements [100..199]
  GET /adCampaigns?start=200&count=100 → returns elements [200..299]
  GET /adCampaigns?start=300&count=100 → returns elements [300..349]
  When len(elements) < count → last page reached

Model B — Token-based (newer LinkedIn endpoints):
  GET /endpoint              → returns elements, nextPageToken="abc123"
  GET /endpoint?pageToken=abc123 → returns next page, nextPageToken="def456"
  When no nextPageToken in response → last page reached
```

**Pagination pseudocode pattern:**

```python
async def paginate_all(client, path, params_base) -> list[dict]:
    """
    Generic paginator — handles both offset and token-based pagination.
    Returns ALL results as a flat list.
    """
    all_results = []
    start = 0
    page_size = 100

    while True:
        # Build params for this page
        params = {**params_base, "start": start, "count": page_size}
        response = await client.get(path, params=params)
        data = response.json()

        elements = data.get("elements", [])
        all_results.extend(elements)

        # STOP CONDITIONS — check both to be safe
        if len(elements) < page_size:
            break  # fewer results than requested → last page

        if "nextPageToken" not in data:
            break  # no token → last page

        start += page_size  # advance offset for next page

    return all_results

# Warning: don't paginate blindly in production
# Always log: "Fetched page {n}, got {len} results, total so far: {total}"
# Silent pagination bugs (stopping too early) are common and hard to detect
```

---

## Section 3 — Efficiency Layer

### 3.1 Incremental Ingestion and High-Water Mark

**The most important efficiency concept for REST API ingestion.**

**Full load vs. incremental load:**

```
FULL LOAD — re-fetch everything every time:
  Every sync: GET all campaigns, all creatives, all metrics
  Pros: Simple. Always complete.
  Cons: Hits API rate limits harder with each new account.
        30 days of daily metrics × 50 campaigns × 10 accounts
        = 15,000 metric rows fetched on every sync.
        Most of it unchanged since yesterday.

INCREMENTAL LOAD — only fetch what's new:
  Every sync: GET metrics only for dates after last_successful_sync
  Pros: Minimal API calls. Scales to hundreds of accounts.
  Cons: Requires tracking "where did we leave off?"
        Misses records that were backdated or retroactively updated.
```

**High-Water Mark — how to track "where we left off":**

```
High-water mark (HWM) = the timestamp or ID of the last record
                         successfully ingested.

Sync run 1 (initial):
  Fetch: date range = [2026-01-01 → 2026-01-31]  (full backfill)
  Result: 31 days of data ingested
  Store HWM: 2026-01-31

Sync run 2 (next day):
  Fetch: date range = [HWM → today] = [2026-01-31 → 2026-02-01]
  Result: 1 day of data fetched
  Store HWM: 2026-02-01

Sync run 3 (next day):
  Fetch: date range = [2026-02-01 → 2026-02-02]
  ...

Each sync only fetches 1-2 days of data instead of 30.
API calls reduced by ~95%.
```

**HWM storage and the overlap problem:**

```
Store the HWM in a sync_log table:
  account_id | last_sync_at        | last_data_date
  acc_123    | 2026-02-01 04:00:00 | 2026-01-31

CRITICAL: Always overlap by 1-2 days.
  Why? LinkedIn's analytics data can be retroactively updated.
  A conversion registered on Feb 1 might adjust Jan 31's cost data.
  If you only fetch from the exact HWM, you miss those adjustments.

  Safe formula:
  fetch_from = last_data_date - timedelta(days=2)  # 2-day overlap
  fetch_to   = date.today()

  This slightly re-fetches data you already have, but your upsert
  logic handles duplicates correctly. The overlap ensures you catch
  retroactive changes.
```

**When full load is still necessary:**

```
Use full load for:
  - Initial ingestion (no HWM exists yet)
  - After a data gap longer than LinkedIn's retention window
  - After a schema migration that requires reprocessing all data
  - Forced reprocessing: delete HWM, pipeline falls back to full load
```

---

### 3.2 Freshness Gate

**What it is:** A check at the START of a sync run that asks "is the data fresh enough that we can skip this run entirely?"

```
Freshness gate decision tree:

Sync triggered (scheduled or on-demand)
          │
          ▼
Is this an on-demand / force_refresh run?
    YES → skip gate, proceed to fetch
    NO  ↓
          ▼
When was the last SUCCESSFUL sync for this account?
    NEVER → proceed to fetch (first-time run)
    ↓
How many minutes ago?
    < 240 min (4 hours) → SKIP. Data is fresh. Log and exit.
    > 240 min           → proceed to fetch
```

**Why this matters at scale:**

```
Without freshness gate (100 accounts, hourly cron):
  100 accounts × 24 hours × 5 API calls per sync
  = 12,000 API calls per day

  LinkedIn's limit: 45M metric values per 5-min window
  That's fine for 1-5 accounts. At 100 it's marginal.
  At 1000 accounts it's a crisis.

With freshness gate (4-hour TTL):
  100 accounts × 6 syncs/day (every 4 hours) × 5 calls
  = 3,000 API calls per day — 75% reduction

  On-demand runs still bypass the gate for immediate freshness.
```

---

### 3.3 Caching

Two distinct caching purposes in an ingestion pipeline:

```
Cache Type 1 — RESULT CACHE (avoid re-fetching from API):
  Stores: full API response or processed snapshot
  Key:    account_id + date_range hash
  TTL:    matches your freshness gate (e.g. 4 hours)
  Where:  Redis or in-process dict
  Use:    When the same data is requested multiple times
          (e.g. dashboard refresh + agent analysis both need same snapshot)

Cache Type 2 — ENTITY ID CACHE (avoid re-fetching reference data):
  Stores: campaign IDs, creative IDs for an account
  Key:    account_id + entity_type
  TTL:    24 hours (campaign/creative structure changes rarely)
  Where:  Redis
  Use:    Metrics fetchers need campaign IDs to build batch requests.
          Without caching, every metrics call also re-fetches the
          campaign list — redundant.
```

**Cache key namespacing — critical for multi-tenant:**

```
WRONG (no tenant isolation):
  cache.set("campaigns", data)
  → Account A's data overwrites Account B's data

CORRECT (fully scoped key):
  cache.set(f"tenant:{tenant_id}:account:{account_id}:campaigns", data)
  → Completely separate cache entries per tenant per account

  Always include: tenant_id + account_id + data_type + optional date_range_hash
```

---

## Section 4 — Data Quality Layer

### 4.1 Pydantic Validation — Your First Line of Defense

**The contract problem:** LinkedIn returns a JSON dict. Nothing guarantees that `dailyBudget` will be a number and not `null`. Nothing guarantees that `status` will be one of your expected values. Without validation, bad data silently flows into your database and corrupts your agents' analysis.

**Pydantic as a data contract:**

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from decimal import Decimal

class LinkedInCampaign(BaseModel):
    """
    This class IS the contract between LinkedIn's API and your pipeline.
    If LinkedIn sends a field you don't recognize → ignored (extra="ignore")
    If LinkedIn sends a field you need in the wrong type → ValidationError raised
    """
    model_config = ConfigDict(
        populate_by_name=True,  # accept both alias and field name
        extra="ignore",         # ignore unknown fields — future-proofing
    )

    # Field(alias=...) handles camelCase → snake_case translation
    id:                          str
    name:                        str
    status:                      Literal["ACTIVE", "PAUSED", "DRAFT", "ARCHIVED"]
    daily_budget_amount:         Decimal | None = Field(None, alias="dailyBudget")
    audience_expansion_enabled:  bool = Field(False, alias="enabledAudienceExpansion")

    @field_validator("daily_budget_amount", mode="before")
    @classmethod
    def parse_budget(cls, v):
        """LinkedIn returns budget as a dict: {"amount": "50.0", "currencyCode": "USD"}"""
        if isinstance(v, dict):
            return v.get("amount")  # extract just the amount
        return v

# Using it:
raw_api_response = {"id": "123", "name": "Test", "status": "ACTIVE",
                    "dailyBudget": {"amount": "50.0", "currencyCode": "USD"},
                    "someNewFieldLinkedInAdded": "ignored"}

campaign = LinkedInCampaign.model_validate(raw_api_response)
# → camelCase translated ✓
# → unknown field ignored ✓
# → budget dict parsed to Decimal ✓
```

**Where to validate — the pipeline insertion points:**

```
LinkedIn API response arrives as raw JSON dict
    │
    ├── INSERTION POINT 1: In the fetcher, immediately after response.json()
    │   Validate each item as a Pydantic model.
    │   Bad records → log + skip (don't crash entire batch)
    │
    ▼
Validated Pydantic objects (typed, safe)
    │
    ├── INSERTION POINT 2: Before writing to database
    │   Convert Pydantic model → SQLModel DB model
    │   Type coercion happens here (Decimal → float for SQLite)
    │
    ▼
SQLModel DB model written to database

Rule: Never write raw dicts to the database. Always go through Pydantic first.
```

---

### 4.2 Schema Evolution

**The problem:** LinkedIn changes their API responses over time. They add new fields, deprecate old ones, occasionally change types. Your pipeline must handle this gracefully — not crash.

**Four types of schema changes and how to handle each:**

```
Change 1 — NEW FIELD ADDED (most common, safest):
  LinkedIn adds "videoViews" to analytics response.
  Your Pydantic model doesn't have this field.
  
  With extra="ignore": new field is silently ignored ✓
  When ready to use it: add the field to your model + run Alembic migration
  Zero downtime. Zero crashes.

──────────────────────────────────────────────────────────────────────

Change 2 — FIELD REMOVED (dangerous):
  LinkedIn removes "relevanceScore" (it happened in 2022).
  Your Pydantic model has relevanceScore: float as required.
  
  Without handling: ValidationError on every record → pipeline stops
  With Optional: relevanceScore: float | None = None → graceful default
  
  Rule: All fields from third-party APIs should be Optional unless
        the API guarantees their presence in writing.

──────────────────────────────────────────────────────────────────────

Change 3 — TYPE CHANGED (rare, most dangerous):
  LinkedIn changes a field from string to object, or int to float.
  
  With field_validator: parse and coerce the value before validation
  Without handling: hard crash

──────────────────────────────────────────────────────────────────────

Change 4 — FIELD RENAMED:
  LinkedIn renames "enabledAudienceExpansion" to "audienceExpansion".
  
  With aliases: accept both old and new names during transition period
  model_config = ConfigDict(populate_by_name=True)
  audience_expansion: bool = Field(alias="audienceExpansion")
  # Also accept the old name via a validator if needed
```

**Alembic for database schema evolution:**

```
When you add a new field to your SQLModel, your database table doesn't
update automatically. Alembic handles this:

1. You add `video_views: int | None = None` to CampaignDailyMetric
2. You run: alembic revision --autogenerate -m "add_video_views"
3. Alembic diffs your model vs. database and generates:
   op.add_column('campaign_daily_metrics',
                 sa.Column('video_views', sa.Integer(), nullable=True))
4. You run: alembic upgrade head
5. Database updated. Old rows have NULL for video_views. New rows get values.

This is the safe way. The alternative — editing the SQL schema string
manually — is error-prone, not versioned, and not reversible.
```

---

### 4.3 Dead Letter Queue (DLQ)

**What it is:** A holding area for records that failed processing. Instead of crashing the pipeline or silently dropping bad data, failed records are stored for later inspection and replay.

```
Normal pipeline flow:
  API response → Validate → Transform → Write to DB ✓

With Dead Letter Queue:
  API response → Validate →
    ┌─── PASS ──► Transform → Write to DB ✓
    └─── FAIL ──► Write to DLQ (with error reason + original payload)

DLQ entry contains:
  - original raw JSON (exactly what came from the API)
  - error type and message ("ValidationError: status='UNKNOWN_VALUE'")
  - timestamp when it failed
  - account_id and run_id for traceability
  - retry_count (how many times this record has been attempted)
```

**When to use DLQ vs. when to skip:**

```
Send to DLQ when:
  - Validation fails on a business-critical field (campaign ID, spend amount)
  - A record fails 3+ times (don't retry indefinitely)
  - The error suggests a systemic issue (new enum value, type change)

Skip (log only) when:
  - A demographic pivot returns empty (expected sometimes)
  - A creative is missing non-critical metadata
  - The record is clearly a test/draft entity

Circuit Breaker + DLQ relationship:
  If DLQ depth exceeds threshold (e.g. >10% of batch failing),
  the pipeline STOPS and alerts — don't silently mask a structural
  problem by shipping bad records to the DLQ indefinitely.
```

**Simple DLQ implementation (database table):**

```
DLQ doesn't require Redis or a message broker.
For your scale, a PostgreSQL table is fine:

Table: ingestion_dead_letters
  id            SERIAL PRIMARY KEY
  account_id    TEXT NOT NULL
  run_id        TEXT NOT NULL
  entity_type   TEXT NOT NULL   -- 'campaign', 'creative', 'metric'
  raw_payload   JSONB NOT NULL  -- original API response
  error_type    TEXT NOT NULL   -- 'ValidationError', 'TransformError'
  error_detail  TEXT NOT NULL   -- human-readable explanation
  retry_count   INT DEFAULT 0
  failed_at     TIMESTAMPTZ NOT NULL
  resolved_at   TIMESTAMPTZ     -- NULL = unresolved
  resolved_by   TEXT            -- 'manual', 'replay', 'auto'

Workflow:
  1. Record fails validation → insert to dead_letters
  2. Engineer reviews dead_letters table weekly
  3. If it's a known LinkedIn quirk → fix the validator, replay
  4. If it's a data quality issue → mark resolved, document
```

---

### 4.4 Idempotency

**Definition:** An operation is idempotent if running it once produces the same result as running it 10 times. Your ingestion pipeline must be idempotent — re-running it must never create duplicates or corrupt existing data.

**Three layers of idempotency:**

```
Layer 1 — API request idempotency:
  GET requests are naturally idempotent (reading doesn't change state)
  LinkedIn's API is read-only for your ingestion → no action needed here

Layer 2 — Write idempotency (most important):
  Use UPSERT (INSERT ON CONFLICT UPDATE) instead of INSERT
  
  NOT idempotent:
    INSERT INTO campaigns (id, name) VALUES ('123', 'Test')
    → Run twice → duplicate row or primary key error
  
  IDEMPOTENT:
    INSERT INTO campaigns (id, name) VALUES ('123', 'Test')
    ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
    → Run twice → same result: one row with latest data ✓

Layer 3 — Run idempotency:
  Assign a unique run_id to every sync run
  Store run_id with every written record
  Rerunning a failed sync with the same date range:
    → Upserts update existing rows rather than creating duplicates
    → Run log records the retry (new run_id, same date range)
```

**The idempotency contract in practice:**

```
Whenever a developer or automated process asks:
"Can I re-run yesterday's sync?"

The answer must always be YES — safely, without manual cleanup.

Checklist:
  ✓ All DB writes use INSERT ON CONFLICT DO UPDATE
  ✓ Composite primary keys prevent duplicate metric rows
    (campaign_id + date = one unique row per campaign per day)
  ✓ created_at is never updated on upsert (only fetched_at changes)
  ✓ Run log records every attempt with status (success/failure/retry)
  ✓ S3 raw storage uses run_id in path — re-runs write to different path,
    old raw files are never overwritten
```

---

## Section 5 — Storage Layer

### 5.1 Write Strategies — Choosing the Right One

Not all writes are the same. The wrong write strategy causes duplicates, data loss, or performance problems.

```
Strategy 1 — INSERT (append only):
  Use when: append-only event logs, audit tables, DLQ entries
  Never use for: entities that can change (campaigns, creatives)
  Risk: Duplicate rows if run twice

Strategy 2 — INSERT OR REPLACE (SQLite) / REPLACE INTO:
  What it does: Deletes the existing row, then inserts a new one
  Use when: You genuinely need to replace everything and have no children
  Risk: Destroys row history. Cascades deletes to child rows.
       created_at is reset. Don't use this for entities.

Strategy 3 — INSERT ON CONFLICT DO UPDATE (true upsert):
  Use when: Everything that can be updated (campaigns, metrics, creatives)
  What it does: Updates ONLY the fields you specify. Row is never deleted.
  Preserves: created_at, foreign key children, row history
  This is the correct choice for ~90% of your ingestion writes.

Strategy 4 — INSERT ON CONFLICT DO NOTHING:
  Use when: You only want to record new data, never update existing
  Example: Snapshot tables where each run's data should be separate
  Risk: Silently ignores conflicts — can mask bugs

Strategy 5 — MERGE / UPSERT with SCD Type 2:
  Use when: You need full history of every change (e.g. bid strategy changes)
  What it does: Closes the old row (valid_to = now), inserts a new row
  Overkill for most of your tables. Consider for campaign settings audit.
```

**Composite primary keys for metrics tables — non-negotiable:**

```
campaign_daily_metrics table:
  PRIMARY KEY (campaign_id, date)
  
This ensures: one row per campaign per day.
If you run the sync twice for the same date range,
the second run UPDATES existing rows (same PK) rather than
inserting duplicates.

Without this: you get N rows per campaign per date,
where N = number of syncs that covered that date range.
Your CTR calculations become wrong immediately.
```

---

### 5.2 Raw Storage (S3/GCS) — The Bronze Layer

**The mental model:** Your database is a processed, queryable view of your data. S3 is the original, immutable record of exactly what LinkedIn sent you.

```
S3 Path Structure (designed for traceability + reprocessing):

raw/
  {tenant_id}/
    {account_id}/
      {YYYY-MM-DD}/          ← date of ingestion (not data date)
        {run_id}/
          accounts.json.gz
          campaigns.json.gz
          creatives.json.gz
          metrics_campaigns.json.gz
          metrics_creatives.json.gz
          demographics.json.gz

Example path:
  raw/tenant_abc/acct_123/2026-02-28/run_xyz789/campaigns.json.gz

Why gzip? Compression is ~80% for JSON.
30 days × 100 accounts × 6 files × ~50KB avg = ~900MB uncompressed
                                               = ~180MB gzipped
Storage cost difference is significant at scale.
```

**Three use cases served by raw storage:**

```
Use Case 1 — Reprocessing without re-hitting API:
  Your Pydantic model was wrong and you need to re-parse all campaigns.
  Without S3: you must re-call LinkedIn API (rate limit cost).
  With S3: read from raw/tenant_abc/acct_123/2026-02-28/run_xyz/campaigns.json.gz
           → re-parse → re-upsert. No API calls. No rate limit impact.

Use Case 2 — LLM context feeding:
  Your LLM agent needs the last 7 days of raw campaign data.
  Option A (database): complex SQL joins, normalized tables
  Option B (S3): read 7 files, decompress, pass raw JSON to LLM
  S3 is often better for LLM consumption — the data is already
  in the shape LinkedIn sent it, with all fields present.

Use Case 3 — Audit / compliance:
  Customer asks "what did our campaigns look like on Feb 15?"
  You can reproduce the exact API response from that date.
  Database may have been updated since. S3 is immutable.
```

**Write order — S3 before database, always:**

```
WRONG ORDER:
  1. Write to database  ← what if step 2 fails?
  2. Write to S3        ← you have DB data but no raw backup

CORRECT ORDER:
  1. Write to S3        ← raw data is safely stored
  2. Write to database  ← if this fails, you can replay from S3

If step 2 fails, you reprocess from S3.
If step 1 fails, the run fails cleanly — nothing was written.
Never have a state where database has data that S3 doesn't.
```

---

## Section 6 — Observability Layer

### 6.1 Structured Logging

**Unstructured log (bad for machines, hard to query):**
```
"Starting sync for account 123456"
"Fetched 47 campaigns"
"Error: 429 Too Many Requests"
```

**Structured log (JSON, queryable, filterable):**
```json
{"level": "INFO",  "event": "sync_started",  "tenant_id": "t_abc", "account_id": "123456", "run_id": "run_xyz", "trigger": "scheduled", "timestamp": "2026-02-28T04:00:01Z"}
{"level": "INFO",  "event": "fetch_complete", "entity": "campaigns", "count": 47, "duration_ms": 234, "run_id": "run_xyz"}
{"level": "WARN",  "event": "rate_limited",   "endpoint": "/adAnalytics", "retry_after": 30, "attempt": 2, "run_id": "run_xyz"}
{"level": "ERROR", "event": "validation_fail", "entity_type": "campaign", "entity_id": "camp_999", "field": "status", "value": "UNKNOWN", "run_id": "run_xyz"}
```

**Why structured logging matters:**
```
Query: "How many validation failures did account 123456 have last week?"
  Unstructured: grep through files, parse manually (hours)
  Structured:   SELECT COUNT(*) WHERE event='validation_fail' AND account_id='123456'
                AND timestamp > now() - interval '7 days' (seconds)

"Which accounts are getting rate limited most often?"
  Structured:   SELECT account_id, COUNT(*) FROM logs WHERE event='rate_limited'
                GROUP BY account_id ORDER BY COUNT(*) DESC
```

**Use `structlog` for Python structured logging:**

```python
import structlog

logger = structlog.get_logger()

# Bind context that applies to all logs in this run
log = logger.bind(
    tenant_id=tenant_id,
    account_id=account_id,
    run_id=run_id
)

# All subsequent calls include tenant_id, account_id, run_id automatically
log.info("sync_started", trigger="scheduled")
log.info("fetch_complete", entity="campaigns", count=47, duration_ms=234)
log.warning("rate_limited", endpoint="/adAnalytics", retry_after=30)
log.error("validation_fail", entity_type="campaign", entity_id="camp_999", field="status")
```

---

### 6.2 Metrics to Emit

Every ingestion pipeline should emit these metrics at minimum. They are your early warning system.

```
THROUGHPUT METRICS:
  records_fetched_total     — total API records received per run
  records_written_total     — total records successfully written to DB
  records_failed_total      — total records sent to DLQ
  api_calls_total           — total LinkedIn API calls made

  Key ratio: records_written / records_fetched
  If this drops below 0.95, you have a data quality problem.

LATENCY METRICS:
  sync_duration_seconds     — how long a full account sync takes
  api_call_duration_ms      — p50, p95, p99 per endpoint

RELIABILITY METRICS:
  sync_success_rate         — successful syncs / total syncs
  rate_limit_hits_total     — 429 responses received
  circuit_breaker_opens     — how often the breaker trips
  retry_count_total         — total retries (high = API is flaky)

FRESHNESS METRICS:
  data_freshness_minutes    — age of most recent data in DB per account
  freshness_gate_hits       — how often syncs are skipped (too fresh)
  last_successful_sync_at   — per account (alert if > 12 hours ago)
```

**Alerting thresholds to configure:**

```
CRITICAL (page someone immediately):
  data_freshness_minutes > 720    (12 hours — data is stale)
  sync_success_rate < 0.80        (80% of syncs failing)
  circuit_breaker_opens > 3/hour  (API is consistently down)

WARNING (investigate within 24 hours):
  records_failed_total > 5% of records_fetched
  rate_limit_hits_total > 20/hour
  sync_duration_seconds > 300     (5 minutes — something is slow)

INFO (track trends):
  api_calls_total per account per day
  freshness_gate_hits (are TTLs well-calibrated?)
```

---

### 6.3 Run Tracking and Data Lineage

**Run tracking answers:** "What happened during this sync?"  
**Data lineage answers:** "Where did this database row come from?"

```
Run tracking table (sync_log):
  run_id            ← unique per execution
  tenant_id
  account_id
  trigger           ← 'scheduled' | 'on_demand' | 'backfill'
  started_at
  finished_at
  status            ← success | partial | failed | skipped
  records_fetched
  records_written
  records_failed
  api_calls_made
  api_calls_retried
  s3_prefix         ← exact S3 path where raw data is stored
  errors            ← JSON array of error summaries

Data lineage (every entity table):
  Add two columns to every table:
  ingested_run_id   ← which run wrote this row
  ingested_at       ← when this row was written

  This lets you answer:
  "This campaign shows a weird CPL spike on Feb 15 —
   which run wrote that data? What raw file did it come from?"
  
  Answer:
  SELECT ingested_run_id FROM campaign_daily_metrics
  WHERE campaign_id='camp_123' AND date='2026-02-15'
  
  → run_id='run_xyz789'
  
  SELECT s3_prefix FROM sync_log WHERE run_id='run_xyz789'
  
  → raw/tenant_abc/acct_123/2026-02-15/run_xyz789/metrics_campaigns.json.gz
  
  Download the raw file, verify the raw data. 5 minutes vs. days of guessing.
```

---

## Section 7 — Quick Reference: Decision Tree

Use this when you're not sure which pattern applies to your situation.

```
PROBLEM: My pipeline is slow (fetches take too long)
  └─► Are you using requests (sync)? → Switch to httpx async
  └─► Are fetches serial? → Use asyncio.gather() + semaphores
  └─► Too many API calls? → Add batching, increase batch size
  └─► Refetching unchanged data? → Add high-water mark + freshness gate

PROBLEM: I'm hitting rate limits (429 errors)
  └─► No rate limiter? → Add Token Bucket per account
  └─► Not respecting Retry-After? → Read header, wait, then retry
  └─► Semaphore too high? → Reduce max_concurrent_accounts
  └─► Batch sizes too large? → Reduce batch size

PROBLEM: Duplicate data in database
  └─► Using INSERT without conflict handling? → Switch to ON CONFLICT DO UPDATE
  └─► No composite primary key on metrics? → Add (campaign_id, date) PK
  └─► No freshness gate? → Add sync_log + should_sync() check

PROBLEM: Bad data crashing my pipeline
  └─► No Pydantic validation? → Add model_validate() at API boundary
  └─► Crashing on one bad record? → Use try/except, send failures to DLQ
  └─► LinkedIn changed a field type? → Make field Optional, add field_validator

PROBLEM: LinkedIn API is down and my whole pipeline stalls
  └─► No circuit breaker? → Add pybreaker wrapper around API calls
  └─► Circuit breaker + retry stacking? → Put breaker outside retry

PROBLEM: Can't reproduce a data issue from last week
  └─► No raw storage? → Add S3 write before DB write
  └─► No run tracking? → Add sync_log table with s3_prefix column
  └─► No lineage columns? → Add ingested_run_id to entity tables
```

---

## Section 8 — Tool Reference

| Tool | Purpose | When to Use |
|---|---|---|
| `httpx` | Async HTTP client | Replace `requests` when you need async |
| `tenacity` | Retry with backoff + jitter | Every external API call |
| `pybreaker` | Circuit breaker | Wrap each external integration point |
| `aiolimiter` | Async token bucket | Rate limiting per account |
| `pyrate-limiter` | Multi-window rate limiting (hourly + daily) | When API has multiple limit tiers |
| `pydantic v2` | Data validation + parsing | All API response models |
| `pydantic-settings` | Typed config from env vars | Replace `os.getenv()` everywhere |
| `sqlmodel` | ORM + Pydantic integration | Database models + queries |
| `alembic` | Schema migrations | Every DB schema change |
| `structlog` | Structured JSON logging | Replace `logging` module |
| `aioboto3` | Async S3 client | Raw storage writes |
| `apscheduler` | Async cron scheduler | Scheduled sync triggers |

---

*This document is a living reference. Update it when new patterns are introduced to the codebase. The goal is that any developer can open this document and understand the "why" behind every architectural decision in the ingestion pipeline.*

---

## Applicability to Node.js Migration

The patterns described in this document -- rate limiting, pagination, batch processing, and retry with exponential backoff -- apply equally to the Node.js migration in `node-app/`. The conceptual approaches are the same; only the implementation primitives differ.

- **HTTP client:** The Node.js implementation uses native `fetch` with `async/await` instead of Python's `httpx`. The same principles of connection pooling, timeouts, and structured error handling apply.
- **Concurrency control:** Concurrency is managed via `p-limit` (a semaphore pattern) instead of Python's `asyncio.Semaphore`. The effect is identical: bounding the number of concurrent API calls to avoid overwhelming the upstream service.
- **Token bucket and circuit breaker:** These patterns can be implemented as needed in the Node.js stack using the same conceptual approach described in Sections 1 and 2 of this document. Libraries such as `bottleneck` (rate limiting) and `opossum` (circuit breaker) serve equivalent roles to Python's `aiolimiter` and `pybreaker`.