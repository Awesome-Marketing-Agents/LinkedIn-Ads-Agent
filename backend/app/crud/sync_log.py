"""CRUD operations for sync_log — freshness gate."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, select

from app.core.config import settings
from app.models.sync import SyncLog
from app.utils.logging import get_logger

logger = get_logger(__name__)


def should_sync(session: Session, account_id: str, force: bool = False) -> tuple[bool, str]:
    if force:
        return True, "force=True"

    ttl = settings.FRESHNESS_TTL_MINUTES
    stmt = (
        select(SyncLog.finished_at)
        .where(SyncLog.account_id == account_id, SyncLog.status == "success")
        .order_by(SyncLog.finished_at.desc())  # type: ignore[union-attr]
        .limit(1)
    )
    row = session.exec(stmt).first()

    if row is None:
        return True, "no previous successful sync"

    last_finished = datetime.fromisoformat(row)
    elapsed = (datetime.now(tz=timezone.utc) - last_finished).total_seconds() / 60
    if elapsed >= ttl:
        return True, f"last sync {elapsed:.0f}m ago (ttl={ttl}m)"
    return False, f"fresh ({elapsed:.0f}m ago, ttl={ttl}m)"


def start_sync_run(
    session: Session, account_id: str, trigger: str = "manual",
) -> int:
    now = datetime.now(tz=timezone.utc).isoformat()
    log = SyncLog(account_id=account_id, started_at=now, trigger=trigger)
    session.add(log)
    session.commit()
    session.refresh(log)
    logger.info("Started sync run %d for account %s", log.id, account_id)
    return log.id  # type: ignore[return-value]


def finish_sync_run(
    session: Session,
    run_id: int,
    status: str = "success",
    stats: dict | None = None,
) -> None:
    stats = stats or {}
    log = session.get(SyncLog, run_id)
    if log is None:
        logger.warning("Sync log %d not found", run_id)
        return

    log.finished_at = datetime.now(tz=timezone.utc).isoformat()
    log.status = status
    log.campaigns_fetched = stats.get("campaigns_fetched", 0)
    log.creatives_fetched = stats.get("creatives_fetched", 0)
    log.api_calls_made = stats.get("api_calls_made", 0)
    log.errors = stats.get("errors")
    session.add(log)
    session.commit()
    logger.info("Finished sync run %d: %s", run_id, status)


def table_counts(session: Session) -> dict[str, int]:
    """Return row counts for every table."""
    from sqlalchemy import text
    tables = [
        "ad_accounts", "campaigns", "creatives",
        "campaign_daily_metrics", "creative_daily_metrics",
        "audience_demographics",
    ]
    counts = {}
    for t in tables:
        result = session.exec(text(f"SELECT COUNT(*) FROM {t}"))  # noqa: S608
        counts[t] = result.one()[0]
    return counts


def active_campaign_audit(session: Session) -> list[dict]:
    """Return active campaigns with potential settings issues."""
    from sqlalchemy import text
    rows = session.exec(text(
        """SELECT name, status, offsite_delivery_enabled, audience_expansion_enabled,
                  cost_type, daily_budget
           FROM campaigns WHERE status = 'ACTIVE'"""
    )).all()

    results = []
    for r in rows:
        issues = []
        if r[2]:  # offsite_delivery_enabled
            issues.append("LAN enabled")
        if r[3]:  # audience_expansion_enabled
            issues.append("Audience Expansion ON")
        if r[4] == "CPM":  # cost_type
            issues.append("Maximum Delivery (CPM)")
        results.append({"name": r[0], "issues": issues})
    return results
