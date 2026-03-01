"""CRUD operations for audience demographics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.models.demographics import AudienceDemographic
from app.utils.logging import get_logger

logger = get_logger(__name__)


def upsert_demographics(
    session: Session, acct: dict, date_range: dict, now: str | None = None,
) -> None:
    now = now or datetime.now(tz=timezone.utc).isoformat()
    for pivot_type, segments in acct.get("audience_demographics", {}).items():
        for seg in segments:
            values = {
                "account_id": acct["id"],
                "pivot_type": pivot_type,
                "segment": seg.get("segment", "?"),
                "impressions": seg.get("impressions", 0),
                "clicks": seg.get("clicks", 0),
                "ctr": seg.get("ctr", 0),
                "share_pct": seg.get("share_of_impressions", 0),
                "date_start": date_range.get("start", ""),
                "date_end": date_range.get("end", ""),
                "fetched_at": now,
            }
            stmt = insert(AudienceDemographic).values(**values)
            update_cols = {
                k: stmt.excluded[k]
                for k in values
                if k not in ("account_id", "pivot_type", "segment", "date_start")
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=["account_id", "pivot_type", "segment", "date_start"],
                set_=update_cols,
            )
            session.exec(stmt)  # type: ignore[call-overload]


def get_demographics(
    session: Session, pivot_type: Optional[str] = None,
) -> list[dict]:
    if pivot_type:
        stmt = (
            select(AudienceDemographic)
            .where(AudienceDemographic.pivot_type == pivot_type)
            .order_by(AudienceDemographic.impressions.desc())  # type: ignore[union-attr]
        )
    else:
        stmt = select(AudienceDemographic).order_by(
            AudienceDemographic.pivot_type,
            AudienceDemographic.impressions.desc(),  # type: ignore[union-attr]
        )
    return [r.model_dump() for r in session.exec(stmt).all()]
