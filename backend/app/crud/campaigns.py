"""CRUD operations for campaigns."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.models.ad_account import AdAccount
from app.models.campaign import Campaign
from app.utils.logging import get_logger

logger = get_logger(__name__)


def upsert_campaign(
    session: Session, account_id: int, camp: dict, now: str | None = None,
) -> None:
    now = now or datetime.now(tz=timezone.utc).isoformat()
    s = camp.get("settings", {})
    values = {
        "id": camp["id"],
        "account_id": account_id,
        "name": camp["name"],
        "status": camp["status"],
        "type": camp.get("type"),
        "daily_budget": float(s.get("daily_budget") or 0),
        "daily_budget_currency": s.get("daily_budget_currency"),
        "total_budget": float(s.get("total_budget") or 0),
        "cost_type": s.get("cost_type"),
        "unit_cost": float(s.get("unit_cost") or 0),
        "bid_strategy": s.get("bid_strategy"),
        "creative_selection": s.get("creative_selection"),
        "offsite_delivery_enabled": s.get("offsite_delivery_enabled", False),
        "audience_expansion_enabled": s.get("audience_expansion_enabled", False),
        "campaign_group": s.get("campaign_group"),
        "created_at": camp.get("created_at"),
        "fetched_at": now,
    }
    stmt = insert(Campaign).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={k: stmt.excluded[k] for k in values if k != "id"},
    )
    session.exec(stmt)  # type: ignore[call-overload]


def get_campaigns(session: Session) -> list[dict]:
    """Return campaigns with account name via JOIN."""
    stmt = (
        select(Campaign, AdAccount.name.label("account_name"))  # type: ignore[attr-defined]
        .outerjoin(AdAccount, Campaign.account_id == AdAccount.id)
        .order_by(Campaign.status, Campaign.name)
    )
    rows = session.exec(stmt).all()
    result = []
    for camp, account_name in rows:
        d = camp.model_dump()
        d["account_name"] = account_name
        result.append(d)
    return result
