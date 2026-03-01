from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel


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
