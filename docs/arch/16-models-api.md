# Module: API Response Models (Pydantic Validation)

## Overview

`models/api_models.py` defines Pydantic models that validate raw JSON responses from the LinkedIn Marketing API before they enter the snapshot assembly and persistence pipeline. These are **Layer 1** models — they sit between the API and your application logic, ensuring only well-formed data flows downstream.

Unknown fields from the API are silently ignored (`extra="ignore"`), and camelCase field names are mapped to snake_case via `alias`.

---

## File Path

`src/linkedin_action_center/models/api_models.py`

---

## Components & Explanation

### Entity Models

- **`LinkedInAccount`** — Validates ad account data from `GET /adAccounts`.
  - Fields: `id` (int), `name` (str), `status` (str), `currency` (Optional), `type` (Optional), `test` (bool, default False).

- **`LinkedInCampaign`** — Validates campaign data from `GET /adAccounts/{id}/adCampaigns`.
  - Fields: `id` (int), `name` (str), `status` (str), `type`, `daily_budget` (nested `_BudgetAmount`), `total_budget`, `cost_type`, `unit_cost`, `optimization_target_type`, `creative_selection`, `offsite_delivery_enabled`, `audience_expansion_enabled`, `campaign_group`, `run_schedule`, `account_id` (internal tag, not from API).
  - Uses aliases for camelCase mapping: `dailyBudget` -> `daily_budget`, `costType` -> `cost_type`, etc.

- **`LinkedInCreative`** — Validates creative data from `GET /adAccounts/{id}/creatives`.
  - Fields: `id` (str), `campaign` (Optional), `intended_status`, `is_serving`, `content` (nested `_ContentBlock`), `serving_hold_reasons`, `created_at`, `last_modified_at`, `account_id` (internal tag).

### Analytics Models

- **`LinkedInAnalyticsRow`** — Validates a single row from `GET /adAnalytics` (CAMPAIGN or CREATIVE pivot).
  - Fields: `pivot_values` (list[str]), `date_range` (nested `_DateRange`), plus 12 metric fields: `impressions`, `clicks`, `cost_in_local_currency`, `landing_page_clicks`, `external_website_conversions`, `likes`, `comments`, `shares`, `follows`, `one_click_leads`, `opens`, `sends`.
  - **`coerce_cost`** validator: Handles string, None, and numeric `costInLocalCurrency` values from the API by coercing to float.

- **`LinkedInDemographicRow`** — Validates a single demographic row.
  - Fields: `pivot_values` (list[str]), `impressions`, `clicks`, `cost_in_local_currency`.
  - Same `coerce_cost` validator.

### Helper Models (private)

- **`_BudgetAmount`** — Nested budget object: `amount` (Optional[str]), `currency_code` (Optional[str], alias `currencyCode`).
- **`_ContentBlock`** — Nested creative content: `reference` (Optional[str]).
- **`_DateRangeBound`** — Date component: `year`, `month`, `day` (all int, default 0).
- **`_DateRange`** — Start/end dates: `start` (_DateRangeBound), `end` (Optional[_DateRangeBound]).

---

## Relationships

- Used by `storage/snapshot.py` in the `_validate_list()` function to gate all incoming API data.
- These models are **not** used for database writes; that's the job of SQLModel models in `models/db_models.py`.
- No dependencies on other project modules (pure Pydantic).

---

## Example Code Snippets

```python
from linkedin_action_center.models.api_models import (
    LinkedInAccount,
    LinkedInCampaign,
    LinkedInAnalyticsRow,
)

# Validate a raw API response
raw_account = {"id": 123, "name": "My Account", "status": "ACTIVE", "unknownField": "ignored"}
account = LinkedInAccount.model_validate(raw_account)
print(account.id, account.name)  # 123 My Account

# Validate campaign with camelCase aliases
raw_campaign = {
    "id": 456,
    "name": "Spring Campaign",
    "status": "ACTIVE",
    "dailyBudget": {"amount": "50.00", "currencyCode": "USD"},
    "costType": "CPC",
}
campaign = LinkedInCampaign.model_validate(raw_campaign)
print(campaign.daily_budget.amount)  # "50.00"
print(campaign.cost_type)            # "CPC"

# Validate analytics row with cost coercion
raw_row = {
    "pivotValues": ["urn:li:sponsoredCampaign:456"],
    "impressions": 1000,
    "clicks": 50,
    "costInLocalCurrency": "125.50",  # string from API
}
row = LinkedInAnalyticsRow.model_validate(raw_row)
print(row.cost_in_local_currency)  # 125.5 (float)
```

```python
# Batch validation (as used in snapshot.py)
from pydantic import ValidationError

valid_items = []
for raw in raw_accounts:
    try:
        LinkedInAccount.model_validate(raw)
        valid_items.append(raw)  # keep original dict
    except ValidationError:
        pass  # logged and skipped
```

---

## Edge Cases & Tips

- **`extra="ignore"`**: Unknown fields from the API are silently dropped. This is intentional — LinkedIn adds new fields frequently, and we don't want validation to break.
- **`populate_by_name=True`**: Allows both the alias (`dailyBudget`) and the Python name (`daily_budget`) when constructing models.
- **Cost coercion**: LinkedIn sometimes returns `costInLocalCurrency` as a string, sometimes as a number, sometimes as `None`. The `coerce_cost` validator handles all cases.
- **Internal tags**: `account_id` on `LinkedInCampaign` and `LinkedInCreative` uses alias `_account_id`. This is set by the CLI/UI callers to tag which account a campaign belongs to — it's not from the LinkedIn API.
- **Validation vs. transformation**: These models validate but the `_validate_list` function returns the **original raw dicts**, not model instances. This preserves all original keys for downstream processing in `assemble_snapshot()`.

---

## Architecture / Flow

```
LinkedIn API -> raw JSON dicts
    |
    └── _validate_list(raw_items, LinkedInAccount, "account")
            ├── LinkedInAccount.model_validate(raw_dict)
            │       ├── Pass? -> keep original dict
            │       └── Fail? -> log warning, skip
            └── return list of valid original dicts
    |
    └── assemble_snapshot() uses validated dicts
```

---

## Advanced Notes

- The two-layer model strategy separates concerns: API models (`api_models.py`) validate incoming data; DB models (`db_models.py`) define the storage schema. They are never mixed.
- `_BudgetAmount.amount` is `Optional[str]` (not float) because LinkedIn returns budget amounts as strings.
- `LinkedInAnalyticsRow` covers 12 metric fields. Missing fields default to 0, so partial API responses don't cause validation failures.
- `_DateRangeBound` defaults all fields to 0 to handle missing date components gracefully.
