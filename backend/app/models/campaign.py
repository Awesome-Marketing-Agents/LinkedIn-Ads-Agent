from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel


class Campaign(SQLModel, table=True):
    __tablename__ = "campaigns"

    id: int = Field(primary_key=True)
    account_id: Optional[int] = Field(default=None, foreign_key="ad_accounts.id")
    name: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    daily_budget: Optional[float] = None
    daily_budget_currency: Optional[str] = None
    total_budget: Optional[float] = None
    cost_type: Optional[str] = None
    unit_cost: Optional[float] = None
    bid_strategy: Optional[str] = None
    creative_selection: Optional[str] = None
    offsite_delivery_enabled: Optional[bool] = None
    audience_expansion_enabled: Optional[bool] = None
    campaign_group: Optional[str] = None
    created_at: Optional[str] = Field(default=None)
    fetched_at: Optional[str] = None
