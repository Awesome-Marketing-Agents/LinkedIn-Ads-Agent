from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel


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
    follows: int = 0
    leads: int = 0
    opens: int = 0
    sends: int = 0
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
    follows: int = 0
    leads: int = 0
    opens: int = 0
    sends: int = 0
    ctr: float = 0.0
    cpc: float = 0.0
    fetched_at: Optional[str] = None
