"""Report routes: campaign/creative metrics, demographics, visual data, accounts, campaigns."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_db
from app.crud.accounts import get_accounts
from app.crud.campaigns import get_campaigns
from app.crud.demographics import get_demographics
from app.crud.metrics import (
    get_campaign_metrics_paginated,
    get_creative_metrics_paginated,
    get_visual_data,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/campaign-metrics")
def campaign_metrics(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_db),
):
    return get_campaign_metrics_paginated(session, page, page_size)


@router.get("/creative-metrics")
def creative_metrics(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_db),
):
    return get_creative_metrics_paginated(session, page, page_size)


@router.get("/demographics")
def demographics(
    pivot_type: str | None = Query(None),
    session: Session = Depends(get_db),
):
    return {"rows": get_demographics(session, pivot_type)}


@router.get("/visual")
def visual_data(session: Session = Depends(get_db)):
    return get_visual_data(session)


@router.get("/campaigns")
def campaigns_list(session: Session = Depends(get_db)):
    return {"rows": get_campaigns(session)}


@router.get("/accounts")
def accounts_list(session: Session = Depends(get_db)):
    accounts = get_accounts(session)
    return {"rows": [a.model_dump() for a in accounts]}
