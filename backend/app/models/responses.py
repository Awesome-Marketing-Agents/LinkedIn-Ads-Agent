"""Shared Pydantic response schemas for the API."""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    rows: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatusResponse(BaseModel):
    token: dict[str, Any]
    database: dict[str, int]
    active_campaign_audit: list[dict[str, Any]]


class VisualReportResponse(BaseModel):
    time_series: list[dict[str, Any]]
    campaign_comparison: list[dict[str, Any]]
    kpis: dict[str, Any]


class SyncJobResponse(BaseModel):
    job_id: str
    status: str


class HealthResponse(BaseModel):
    status: str = "ok"
    database: Optional[str] = None
