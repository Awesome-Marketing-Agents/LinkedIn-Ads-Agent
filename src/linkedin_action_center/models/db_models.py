"""SQLModel table definitions mirroring the SQLite schema.

These models serve as the authoritative schema definition and are consumed
by Alembic for migration generation.  They deliberately mirror the existing
raw-SQL schema in ``storage/database.py`` so that ``alembic upgrade head``
on an existing database is a no-op.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


# ---------------------------------------------------------------------------
# Entity tables
# ---------------------------------------------------------------------------

class AdAccount(SQLModel, table=True):
    __tablename__ = "ad_accounts"

    id: int = Field(primary_key=True)
    name: Optional[str] = None
    status: Optional[str] = None
    currency: Optional[str] = None
    type: Optional[str] = None
    is_test: Optional[bool] = None
    created_at: Optional[str] = Field(default=None)
    fetched_at: Optional[str] = None


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


class Creative(SQLModel, table=True):
    __tablename__ = "creatives"

    id: str = Field(primary_key=True)
    campaign_id: Optional[int] = Field(default=None, foreign_key="campaigns.id")
    account_id: Optional[int] = Field(default=None, foreign_key="ad_accounts.id")
    intended_status: Optional[str] = None
    is_serving: Optional[bool] = None
    content_reference: Optional[str] = None
    created_at: Optional[int] = None
    last_modified_at: Optional[int] = None
    fetched_at: Optional[str] = None


class CampaignDailyMetric(SQLModel, table=True):
    __tablename__ = "campaign_daily_metrics"

    campaign_id: int = Field(primary_key=True, foreign_key="campaigns.id")
    date: str = Field(primary_key=True)
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    landing_page_clicks: int = 0
    conversions: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    ctr: float = 0.0
    cpc: float = 0.0
    fetched_at: Optional[str] = None


class CreativeDailyMetric(SQLModel, table=True):
    __tablename__ = "creative_daily_metrics"

    creative_id: str = Field(primary_key=True, foreign_key="creatives.id")
    date: str = Field(primary_key=True)
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    landing_page_clicks: int = 0
    conversions: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    ctr: float = 0.0
    cpc: float = 0.0
    fetched_at: Optional[str] = None


class AudienceDemographic(SQLModel, table=True):
    __tablename__ = "audience_demographics"

    account_id: int = Field(primary_key=True, foreign_key="ad_accounts.id")
    pivot_type: str = Field(primary_key=True)
    segment: str = Field(primary_key=True)
    date_start: str = Field(primary_key=True)
    impressions: int = 0
    clicks: int = 0
    ctr: float = 0.0
    share_pct: float = 0.0
    date_end: Optional[str] = None
    fetched_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Sync log
# ---------------------------------------------------------------------------

class SyncLog(SQLModel, table=True):
    __tablename__ = "sync_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: str
    started_at: str
    finished_at: Optional[str] = None
    status: str = "running"
    trigger: Optional[str] = None
    campaigns_fetched: int = 0
    creatives_fetched: int = 0
    api_calls_made: int = 0
    errors: Optional[str] = None
