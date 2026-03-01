from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Column
from sqlmodel import Field, SQLModel


class Creative(SQLModel, table=True):
    __tablename__ = "creatives"

    id: str = Field(primary_key=True)
    campaign_id: Optional[int] = Field(default=None, foreign_key="campaigns.id")
    account_id: Optional[int] = Field(default=None, foreign_key="ad_accounts.id")
    intended_status: Optional[str] = None
    is_serving: Optional[bool] = None
    content_reference: Optional[str] = None
    serving_hold_reasons: Optional[str] = None
    created_at: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    last_modified_at: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    fetched_at: Optional[str] = None
