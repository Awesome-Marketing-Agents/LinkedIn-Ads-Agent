from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel


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
