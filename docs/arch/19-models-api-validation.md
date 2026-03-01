# Module: LinkedIn API Response Models

## Overview

Pydantic models that validate raw JSON responses from the LinkedIn Marketing REST API before data enters the persistence pipeline. Unknown fields are silently ignored (`extra="ignore"`), and CamelCase API fields are mapped to snake_case via aliases.

---

## File Path

`backend/app/models/linkedin_api.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `pydantic.BaseModel` | Model base class |
| `pydantic.ConfigDict` | Model configuration |
| `pydantic.Field` | Aliases and defaults |
| `pydantic.field_validator` | Cost coercion |

---

## Components

### `LinkedInAccount`

| Field | Type | Alias | Default |
|-------|------|-------|---------|
| `id` | `int` | — | required |
| `name` | `str` | — | required |
| `status` | `str` | — | required |
| `currency` | `Optional[str]` | — | `None` |
| `type` | `Optional[str]` | — | `None` |
| `test` | `bool` | — | `False` |

### `LinkedInCampaign`

| Field | Type | Alias | Default |
|-------|------|-------|---------|
| `id` | `int` | — | required |
| `name` | `str` | — | required |
| `status` | `str` | — | required |
| `type` | `Optional[str]` | — | `None` |
| `daily_budget` | `Optional[_BudgetAmount]` | `dailyBudget` | `None` |
| `total_budget` | `Optional[_BudgetAmount]` | `totalBudget` | `None` |
| `cost_type` | `Optional[str]` | `costType` | `None` |
| `unit_cost` | `Optional[_BudgetAmount]` | `unitCost` | `None` |
| `optimization_target_type` | `Optional[str]` | `optimizationTargetType` | `None` |
| `creative_selection` | `Optional[str]` | `creativeSelection` | `None` |
| `offsite_delivery_enabled` | `bool` | `offsiteDeliveryEnabled` | `False` |
| `audience_expansion_enabled` | `bool` | `audienceExpansionEnabled` | `False` |
| `campaign_group` | `Optional[str]` | `campaignGroup` | `None` |
| `run_schedule` | `Optional[Any]` | `runSchedule` | `None` |
| `account_id` | `Optional[int]` | `_account_id` | `None` |

**Helper**: `_BudgetAmount` has `amount: Optional[str]` and `currency_code: Optional[str]` (alias `currencyCode`).

### `LinkedInCreative`

| Field | Type | Alias | Default |
|-------|------|-------|---------|
| `id` | `str` | — | required |
| `campaign` | `Optional[str]` | — | `None` |
| `intended_status` | `Optional[str]` | `intendedStatus` | `None` |
| `is_serving` | `bool` | `isServing` | `False` |
| `content` | `Optional[_ContentBlock]` | — | `None` |
| `serving_hold_reasons` | `Optional[list[str]]` | `servingHoldReasons` | `None` |
| `created_at` | `Optional[int]` | `createdAt` | `None` |
| `last_modified_at` | `Optional[int]` | `lastModifiedAt` | `None` |
| `account_id` | `Optional[int]` | `_account_id` | `None` |

**Helper**: `_ContentBlock` has `reference: Optional[str]`.

### `LinkedInAnalyticsRow`

| Field | Type | Alias | Default |
|-------|------|-------|---------|
| `pivot_values` | `list[str]` | `pivotValues` | `[]` |
| `date_range` | `Optional[_DateRange]` | `dateRange` | `None` |
| `impressions` | `int` | — | `0` |
| `clicks` | `int` | — | `0` |
| `cost_in_local_currency` | `float` | `costInLocalCurrency` | `0.0` |
| `landing_page_clicks` | `int` | `landingPageClicks` | `0` |
| `external_website_conversions` | `int` | `externalWebsiteConversions` | `0` |
| `likes` | `int` | — | `0` |
| `comments` | `int` | — | `0` |
| `shares` | `int` | — | `0` |
| `follows` | `int` | — | `0` |
| `one_click_leads` | `int` | `oneClickLeads` | `0` |
| `opens` | `int` | — | `0` |
| `sends` | `int` | — | `0` |

**Helpers**: `_DateRangeBound` has `year`, `month`, `day` (int, default 0). `_DateRange` has `start: _DateRangeBound` and `end: Optional[_DateRangeBound]`.

**Validator**: `coerce_cost` — handles `None`, empty string, and numeric values for `cost_in_local_currency`.

### `LinkedInDemographicRow`

| Field | Type | Alias | Default |
|-------|------|-------|---------|
| `pivot_values` | `list[str]` | `pivotValues` | `[]` |
| `impressions` | `int` | — | `0` |
| `clicks` | `int` | — | `0` |
| `cost_in_local_currency` | `float` | `costInLocalCurrency` | `0.0` |

Also has the `coerce_cost` validator.

---

## Design Decisions

- **`extra="ignore"`**: Forward-compatible with LinkedIn API changes — new fields don't break validation
- **`populate_by_name=True`**: Allows using both Python names and API aliases
- **`coerce_cost`**: LinkedIn returns cost as string, number, empty string, or null depending on context

---

## Code Snippet

```python
from app.models.linkedin_api import LinkedInCampaign

raw = {"id": 123, "name": "Test", "status": "ACTIVE", "dailyBudget": {"amount": "50.00"}}
campaign = LinkedInCampaign.model_validate(raw)
print(campaign.daily_budget.amount)  # "50.00"
```

---

## Relationships

- **Used by**: `services/snapshot.py` for validation gate (`_validate_list()`)
