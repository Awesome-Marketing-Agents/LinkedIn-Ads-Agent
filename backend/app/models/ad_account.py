from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel


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
