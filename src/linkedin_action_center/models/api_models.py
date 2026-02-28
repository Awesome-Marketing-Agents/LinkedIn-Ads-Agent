"""Pydantic models for LinkedIn Marketing API responses (Layer 1).

These models validate raw JSON coming from the LinkedIn REST API before it
enters the snapshot assembly and persistence pipeline.  Unknown fields are
silently ignored (``extra="ignore"``), and camelCase field names from the API
are mapped to snake_case via ``alias``.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LinkedInAccount(BaseModel):
    """Represents a LinkedIn Ad Account from ``GET /adAccounts``."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: int
    name: str
    status: str
    currency: Optional[str] = None
    type: Optional[str] = None
    test: bool = False


class _BudgetAmount(BaseModel):
    """Nested budget object (``{amount, currencyCode}``)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    amount: Optional[str] = None
    currency_code: Optional[str] = Field(default=None, alias="currencyCode")


class LinkedInCampaign(BaseModel):
    """Represents a LinkedIn Campaign from ``GET /adAccounts/{id}/adCampaigns``."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: int
    name: str
    status: str
    type: Optional[str] = None
    daily_budget: Optional[_BudgetAmount] = Field(default=None, alias="dailyBudget")
    total_budget: Optional[_BudgetAmount] = Field(default=None, alias="totalBudget")
    cost_type: Optional[str] = Field(default=None, alias="costType")
    unit_cost: Optional[_BudgetAmount] = Field(default=None, alias="unitCost")
    optimization_target_type: Optional[str] = Field(
        default=None, alias="optimizationTargetType",
    )
    creative_selection: Optional[str] = Field(default=None, alias="creativeSelection")
    offsite_delivery_enabled: bool = Field(default=False, alias="offsiteDeliveryEnabled")
    audience_expansion_enabled: bool = Field(
        default=False, alias="audienceExpansionEnabled",
    )
    campaign_group: Optional[str] = Field(default=None, alias="campaignGroup")
    run_schedule: Optional[Any] = Field(default=None, alias="runSchedule")

    # Internal tag added by CLI/UI callers — not from the API
    account_id: Optional[int] = Field(default=None, alias="_account_id")


class _ContentBlock(BaseModel):
    """Nested ``content`` object on a creative."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    reference: Optional[str] = None


class LinkedInCreative(BaseModel):
    """Represents a LinkedIn Creative from ``GET /adAccounts/{id}/creatives``."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str
    campaign: Optional[str] = None
    intended_status: Optional[str] = Field(default=None, alias="intendedStatus")
    is_serving: bool = Field(default=False, alias="isServing")
    content: Optional[_ContentBlock] = None
    serving_hold_reasons: Optional[list[str]] = Field(
        default=None, alias="servingHoldReasons",
    )
    created_at: Optional[int] = Field(default=None, alias="createdAt")
    last_modified_at: Optional[int] = Field(default=None, alias="lastModifiedAt")

    # Internal tag added by CLI/UI callers
    account_id: Optional[int] = Field(default=None, alias="_account_id")


class _DateRangeBound(BaseModel):
    """``{year, month, day}`` component of a LinkedIn dateRange."""

    model_config = ConfigDict(extra="ignore")

    year: int = 0
    month: int = 0
    day: int = 0


class _DateRange(BaseModel):
    """``{start: {year, month, day}, end: ...}``."""

    model_config = ConfigDict(extra="ignore")

    start: _DateRangeBound = Field(default_factory=_DateRangeBound)
    end: Optional[_DateRangeBound] = None


class LinkedInAnalyticsRow(BaseModel):
    """A single row from ``GET /adAnalytics`` (CAMPAIGN or CREATIVE pivot)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    pivot_values: list[str] = Field(default_factory=list, alias="pivotValues")
    date_range: Optional[_DateRange] = Field(default=None, alias="dateRange")

    impressions: int = 0
    clicks: int = 0
    cost_in_local_currency: float = Field(default=0.0, alias="costInLocalCurrency")
    landing_page_clicks: int = Field(default=0, alias="landingPageClicks")
    external_website_conversions: int = Field(
        default=0, alias="externalWebsiteConversions",
    )
    likes: int = 0
    comments: int = 0
    shares: int = 0
    follows: int = 0
    one_click_leads: int = Field(default=0, alias="oneClickLeads")
    opens: int = 0
    sends: int = 0

    @field_validator("cost_in_local_currency", mode="before")
    @classmethod
    def coerce_cost(cls, v: Any) -> float:
        """Handle string, None, and numeric cost values from the API."""
        if v is None or v == "":
            return 0.0
        return float(v)


class LinkedInDemographicRow(BaseModel):
    """A single row from ``GET /adAnalytics`` with a demographic pivot."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    pivot_values: list[str] = Field(default_factory=list, alias="pivotValues")
    impressions: int = 0
    clicks: int = 0
    cost_in_local_currency: float = Field(default=0.0, alias="costInLocalCurrency")

    @field_validator("cost_in_local_currency", mode="before")
    @classmethod
    def coerce_cost(cls, v: Any) -> float:
        if v is None or v == "":
            return 0.0
        return float(v)
