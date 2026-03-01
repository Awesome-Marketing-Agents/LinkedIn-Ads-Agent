"""CRUD operations for campaign/creative metrics + visual aggregation queries."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.models.campaign import Campaign
from app.models.creative import Creative
from app.models.metrics import CampaignDailyMetric, CreativeDailyMetric
from app.utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Upserts
# ---------------------------------------------------------------------------

def upsert_campaign_daily_metrics(
    session: Session, camp: dict, now: str | None = None,
) -> None:
    now = now or datetime.now(tz=timezone.utc).isoformat()
    rows = camp.get("daily_metrics", [])
    if not rows:
        return

    for day in rows:
        values = {
            "campaign_id": camp["id"],
            "date": day["date"],
            "impressions": day.get("impressions", 0),
            "clicks": day.get("clicks", 0),
            "spend": day.get("spend", 0),
            "landing_page_clicks": day.get("landing_page_clicks", 0),
            "conversions": day.get("conversions", 0),
            "likes": day.get("likes", 0),
            "comments": day.get("comments", 0),
            "shares": day.get("shares", 0),
            "follows": day.get("follows", 0),
            "leads": day.get("leads", 0),
            "opens": day.get("opens", 0),
            "sends": day.get("sends", 0),
            "ctr": day.get("ctr", 0),
            "cpc": day.get("cpc", 0),
            "fetched_at": now,
        }
        stmt = insert(CampaignDailyMetric).values(**values)
        update_cols = {k: stmt.excluded[k] for k in values if k not in ("campaign_id", "date")}
        stmt = stmt.on_conflict_do_update(
            index_elements=["campaign_id", "date"],
            set_=update_cols,
        )
        session.exec(stmt)  # type: ignore[call-overload]


def upsert_creative_daily_metrics(
    session: Session, creative: dict, now: str | None = None,
) -> None:
    now = now or datetime.now(tz=timezone.utc).isoformat()
    rows = creative.get("daily_metrics", [])
    if not rows:
        return

    for day in rows:
        values = {
            "creative_id": creative["id"],
            "date": day["date"],
            "impressions": day.get("impressions", 0),
            "clicks": day.get("clicks", 0),
            "spend": day.get("spend", 0),
            "landing_page_clicks": day.get("landing_page_clicks", 0),
            "conversions": day.get("conversions", 0),
            "likes": day.get("likes", 0),
            "comments": day.get("comments", 0),
            "shares": day.get("shares", 0),
            "follows": day.get("follows", 0),
            "leads": day.get("leads", 0),
            "opens": day.get("opens", 0),
            "sends": day.get("sends", 0),
            "ctr": day.get("ctr", 0),
            "cpc": day.get("cpc", 0),
            "fetched_at": now,
        }
        stmt = insert(CreativeDailyMetric).values(**values)
        update_cols = {k: stmt.excluded[k] for k in values if k not in ("creative_id", "date")}
        stmt = stmt.on_conflict_do_update(
            index_elements=["creative_id", "date"],
            set_=update_cols,
        )
        session.exec(stmt)  # type: ignore[call-overload]


def upsert_creatives(
    session: Session, account_id: int, camp: dict, now: str | None = None,
) -> None:
    now = now or datetime.now(tz=timezone.utc).isoformat()
    for cr in camp.get("creatives", []):
        hold_reasons = cr.get("serving_hold_reasons")
        if isinstance(hold_reasons, list):
            hold_reasons = ",".join(hold_reasons) if hold_reasons else None
        values = {
            "id": cr.get("id", ""),
            "campaign_id": camp["id"],
            "account_id": account_id,
            "intended_status": cr.get("intended_status"),
            "is_serving": cr.get("is_serving", False),
            "content_reference": cr.get("content_reference"),
            "content_name": cr.get("content_name"),
            "serving_hold_reasons": hold_reasons,
            "created_at": cr.get("created_at"),
            "last_modified_at": cr.get("last_modified_at"),
            "fetched_at": now,
        }
        stmt = insert(Creative).values(**values)
        update_cols = {k: stmt.excluded[k] for k in values if k not in ("id", "created_at")}
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=update_cols)
        session.exec(stmt)  # type: ignore[call-overload]


# ---------------------------------------------------------------------------
# Paginated queries
# ---------------------------------------------------------------------------

def get_campaign_metrics_paginated(
    session: Session, page: int = 1, page_size: int = 50,
) -> dict:
    total = session.exec(
        select(func.count()).select_from(CampaignDailyMetric)
    ).one()
    offset = (page - 1) * page_size

    stmt = (
        select(CampaignDailyMetric, Campaign.name.label("campaign_name"))  # type: ignore[attr-defined]
        .outerjoin(Campaign, CampaignDailyMetric.campaign_id == Campaign.id)
        .order_by(CampaignDailyMetric.date.desc(), CampaignDailyMetric.campaign_id)  # type: ignore[union-attr]
        .offset(offset)
        .limit(page_size)
    )
    rows = session.exec(stmt).all()
    result = []
    for metric, campaign_name in rows:
        d = metric.model_dump()
        d["campaign_name"] = campaign_name
        result.append(d)

    return {
        "rows": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total else 0,
    }


def get_creative_metrics_paginated(
    session: Session, page: int = 1, page_size: int = 50,
) -> dict:
    total = session.exec(
        select(func.count()).select_from(CreativeDailyMetric)
    ).one()
    offset = (page - 1) * page_size

    stmt = (
        select(
            CreativeDailyMetric,
            Creative.content_name.label("content_name"),  # type: ignore[attr-defined]
            Campaign.name.label("campaign_name"),  # type: ignore[attr-defined]
        )
        .outerjoin(Creative, CreativeDailyMetric.creative_id == Creative.id)
        .outerjoin(Campaign, Creative.campaign_id == Campaign.id)
        .order_by(CreativeDailyMetric.date.desc(), CreativeDailyMetric.creative_id)  # type: ignore[union-attr]
        .offset(offset)
        .limit(page_size)
    )
    rows = session.exec(stmt).all()
    result = []
    for metric, content_name, campaign_name in rows:
        d = metric.model_dump()
        d["content_name"] = content_name
        d["campaign_name"] = campaign_name
        result.append(d)

    return {
        "rows": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total else 0,
    }


def get_creatives(session: Session) -> list[dict]:
    """Return all creatives with campaign name via JOIN."""
    stmt = (
        select(Creative, Campaign.name.label("campaign_name"))  # type: ignore[attr-defined]
        .outerjoin(Campaign, Creative.campaign_id == Campaign.id)
        .order_by(Creative.last_modified_at.desc())  # type: ignore[union-attr]
    )
    rows = session.exec(stmt).all()
    result = []
    for cr, campaign_name in rows:
        d = cr.model_dump()
        d["campaign_name"] = campaign_name
        result.append(d)
    return result


# ---------------------------------------------------------------------------
# Visual aggregation queries
# ---------------------------------------------------------------------------

def get_visual_data(session: Session) -> dict:
    # Time series
    time_series = session.exec(text(
        """SELECT date, SUM(impressions) as impressions, SUM(clicks) as clicks,
                  SUM(spend) as spend, SUM(conversions) as conversions
           FROM campaign_daily_metrics
           GROUP BY date ORDER BY date"""
    )).all()

    # Campaign comparison
    campaign_comparison = session.exec(text(
        """SELECT c.name, SUM(cdm.impressions) as impressions, SUM(cdm.clicks) as clicks,
                  SUM(cdm.spend) as spend, SUM(cdm.conversions) as conversions
           FROM campaign_daily_metrics cdm
           JOIN campaigns c ON cdm.campaign_id = c.id
           GROUP BY cdm.campaign_id, c.name
           ORDER BY SUM(cdm.spend) DESC"""
    )).all()

    # Summary KPIs
    summary = session.exec(text(
        """SELECT COALESCE(SUM(impressions), 0) as total_impressions,
                  COALESCE(SUM(clicks), 0) as total_clicks,
                  COALESCE(SUM(spend), 0) as total_spend,
                  COALESCE(SUM(conversions), 0) as total_conversions
           FROM campaign_daily_metrics"""
    )).one()

    total_imp = summary[0]
    total_clk = summary[1]
    total_spend = summary[2]
    total_conv = summary[3]

    return {
        "time_series": [
            {"date": r[0], "impressions": r[1], "clicks": r[2], "spend": r[3], "conversions": r[4]}
            for r in time_series
        ],
        "campaign_comparison": [
            {"name": r[0], "impressions": r[1], "clicks": r[2], "spend": r[3], "conversions": r[4]}
            for r in campaign_comparison
        ],
        "kpis": {
            "impressions": total_imp,
            "clicks": total_clk,
            "spend": round(total_spend, 2),
            "conversions": total_conv,
            "ctr": round((total_clk / total_imp) * 100, 4) if total_imp else 0,
            "cpc": round(total_spend / total_clk, 2) if total_clk else 0,
            "cpm": round((total_spend / total_imp) * 1000, 2) if total_imp else 0,
        },
    }
