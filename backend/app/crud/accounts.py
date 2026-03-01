"""CRUD operations for ad accounts."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.models.ad_account import AdAccount
from app.utils.logging import get_logger

logger = get_logger(__name__)


def upsert_account(session: Session, acct: dict, now: str | None = None) -> None:
    now = now or datetime.now(tz=timezone.utc).isoformat()
    values = {
        "id": acct["id"],
        "name": acct["name"],
        "status": acct["status"],
        "currency": acct.get("currency"),
        "type": acct.get("type"),
        "is_test": acct.get("test", False),
        "fetched_at": now,
    }
    stmt = insert(AdAccount).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={k: stmt.excluded[k] for k in values if k != "id"},
    )
    session.exec(stmt)  # type: ignore[call-overload]


def get_accounts(session: Session) -> list[AdAccount]:
    return list(session.exec(select(AdAccount).order_by(AdAccount.name)).all())
