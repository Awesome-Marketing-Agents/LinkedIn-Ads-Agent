# Module: Status & Health Routes

## Overview

Status provides a system dashboard (token health, database counts, campaign audit). Health provides a lightweight database connectivity check.

---

## File Paths

- `backend/app/routes/status.py`
- `backend/app/routes/health.py`

---

## Components — status.py

### `GET /status`

```python
def status(
    session: Session = Depends(get_db),
    auth: AuthManager = Depends(get_auth),
):
```

**Purpose**: Combined system status endpoint.

**Returns**:
```python
{
    "token": {"authenticated": true, "access_token_days_remaining": 45, ...},
    "database": {"ad_accounts": 2, "campaigns": 15, "creatives": 42, ...},
    "active_campaign_audit": [{"name": "Campaign A", "issues": ["LAN enabled"]}],
}
```

**Error handling**: If `table_counts()` or `active_campaign_audit()` raise, returns fallback values (`{"error": -1}` and `[]`).

---

## Components — health.py

### `GET /health`

```python
def health(session: Session = Depends(get_db)):
```

**Purpose**: Lightweight database connectivity check.

**Behavior**: Executes `SELECT 1`. Returns `{"status": "ok", "database": "connected"}` on success, `{"status": "degraded", "database": "<error>"}` on failure.

---

## Relationships

- **Mounted by**: `routes/__init__.py` at `/status` and `/health`
- **Calls**: `crud/sync_log.py` for table counts and audit, `core/security.py` for token status
