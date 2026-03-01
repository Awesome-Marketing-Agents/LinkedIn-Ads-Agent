# Module: Report Routes

## Overview

Report routes serve read-only data queries for the frontend dashboard. Seven GET endpoints provide paginated metrics, demographics, visual aggregation data, and entity lists.

---

## File Path

`backend/app/routes/report.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `app.core.deps.get_db` | Database session injection |
| `app.crud.accounts.get_accounts` | Account query |
| `app.crud.campaigns.get_campaigns` | Campaign query with JOIN |
| `app.crud.demographics.get_demographics` | Demographics query |
| `app.crud.metrics` | Paginated metrics + visual data |

---

## Components

### `GET /report/campaign-metrics`

```python
def campaign_metrics(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_db),
):
```

**Returns**: Paginated campaign daily metrics with `campaign_name`.

### `GET /report/creative-metrics`

Same pagination pattern. Returns creative metrics with `content_name` and `campaign_name`.

### `GET /report/demographics`

```python
def demographics(
    pivot_type: str | None = Query(None),
    session: Session = Depends(get_db),
):
```

**Returns**: `{"rows": [...]}` — demographics filtered by optional `pivot_type`.

### `GET /report/visual`

```python
def visual_data(session: Session = Depends(get_db)):
    return get_visual_data(session)
```

**Returns**: `{"time_series": [...], "campaign_comparison": [...], "kpis": {...}}`.

### `GET /report/creatives`

**Returns**: `{"rows": [...]}` — all creatives with `campaign_name`.

### `GET /report/campaigns`

**Returns**: `{"rows": [...]}` — all campaigns with `account_name`.

### `GET /report/accounts`

**Returns**: `{"rows": [...]}` — all accounts (model_dump).

---

## Design Notes

- All routes use sync `def` (not `async def`) since they only do database I/O — FastAPI runs them in a threadpool automatically
- Pagination defaults: page 1, 50 rows, max 200

---

## Relationships

- **Mounted by**: `routes/__init__.py` at `/report`
- **Calls**: `crud/` query functions — see [15](15-crud-accounts-campaigns.md), [16](16-crud-metrics-demographics.md)
