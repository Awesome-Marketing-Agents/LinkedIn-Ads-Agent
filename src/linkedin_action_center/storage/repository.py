"""Data-access layer: upsert and query helpers for the LinkedIn Ads SQLite DB.

The public API is ``persist_snapshot(snapshot_dict)`` which writes an entire
assembled snapshot into the normalised tables using SQLAlchemy Core
``insert().on_conflict_do_update()`` for true upserts.

Also provides a freshness gate via ``should_sync`` / ``start_sync_run`` /
``finish_sync_run`` backed by the ``sync_log`` table.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.dialects.sqlite import insert
from sqlmodel import Session, select

from linkedin_action_center.core.config import settings
from linkedin_action_center.models.db_models import (
    AdAccount,
    AudienceDemographic,
    Campaign,
    CampaignDailyMetric,
    Creative,
    CreativeDailyMetric,
    SyncLog,
)
from linkedin_action_center.storage.database import get_connection, get_engine
from linkedin_action_center.utils.errors import StorageError
from linkedin_action_center.utils.logger import logger


# ---------------------------------------------------------------------------
# Freshness gate
# ---------------------------------------------------------------------------

def should_sync(
    account_id: str,
    force: bool = False,
    db_path: Path | None = None,
) -> tuple[bool, str]:
    """Decide whether a sync is needed for *account_id*.

    Returns ``(True, reason)`` when a sync should proceed, or
    ``(False, reason)`` when the data is still fresh.
    """
    if force:
        return True, "force=True"

    ttl = settings.freshness_ttl_minutes
    conn = get_connection(db_path)
    cur = conn.cursor()
    row = cur.execute(
        """SELECT finished_at FROM sync_log
           WHERE account_id = ? AND status = 'success'
           ORDER BY finished_at DESC LIMIT 1""",
        (str(account_id),),
    ).fetchone()
    conn.close()

    if row is None:
        return True, "no previous successful sync"

    last_finished = datetime.fromisoformat(row[0])
    elapsed = (datetime.now(tz=timezone.utc) - last_finished).total_seconds() / 60
    if elapsed >= ttl:
        return True, f"last sync {elapsed:.0f}m ago (ttl={ttl}m)"
    return False, f"fresh ({elapsed:.0f}m ago, ttl={ttl}m)"


def start_sync_run(
    account_id: str,
    trigger: str = "manual",
    db_path: Path | None = None,
) -> int:
    """Insert a new ``sync_log`` row with status='running'. Returns the row id."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now(tz=timezone.utc).isoformat()
    cur.execute(
        "INSERT INTO sync_log (account_id, started_at, status, trigger) VALUES (?,?,?,?)",
        (str(account_id), now, "running", trigger),
    )
    run_id = cur.lastrowid
    conn.commit()
    conn.close()
    return run_id


def finish_sync_run(
    run_id: int,
    status: str = "success",
    stats: dict | None = None,
    db_path: Path | None = None,
) -> None:
    """Update an existing ``sync_log`` row with final status and stats."""
    stats = stats or {}
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now(tz=timezone.utc).isoformat()
    cur.execute(
        """UPDATE sync_log
           SET finished_at = ?, status = ?,
               campaigns_fetched = ?, creatives_fetched = ?,
               api_calls_made = ?, errors = ?
           WHERE id = ?""",
        (
            now,
            status,
            stats.get("campaigns_fetched", 0),
            stats.get("creatives_fetched", 0),
            stats.get("api_calls_made", 0),
            stats.get("errors"),
            run_id,
        ),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Snapshot persistence (SQLAlchemy Core upsert)
# ---------------------------------------------------------------------------

def persist_snapshot(snap: dict, db_path: Path | None = None) -> None:
    """Write the full snapshot dict into SQLite (true upsert pattern).

    The public signature is unchanged — callers pass a plain dict.
    Internally we use SQLAlchemy Core ``insert().on_conflict_do_update()``
    for each table.
    """
    try:
        # Ensure schema is created (legacy path for tests using db_path)
        if db_path is not None:
            conn = get_connection(db_path)
            conn.close()
            engine = get_engine(f"sqlite:///{db_path}")
        else:
            conn = get_connection()
            conn.close()
            engine = get_engine()

        now = datetime.now(tz=timezone.utc).isoformat()

        with Session(engine) as session:
            for acct in snap.get("accounts", []):
                _upsert_account(session, acct, now)

                for camp in acct.get("campaigns", []):
                    _upsert_campaign(session, acct["id"], camp, now)
                    _upsert_campaign_daily_metrics(session, camp, now)
                    _upsert_creatives(session, acct["id"], camp, now)

                _upsert_demographics(session, acct, snap.get("date_range", {}), now)

            session.commit()
    except Exception as e:
        logger.error(f"Database error while persisting snapshot: {e}")
        raise StorageError(
            "Failed to persist snapshot to database",
            operation="persist_snapshot",
            table="multiple",
        ) from e


# ---------------------------------------------------------------------------
# Private upsert helpers — SQLAlchemy Core insert().on_conflict_do_update()
# ---------------------------------------------------------------------------

def _upsert_account(session: Session, acct: dict, now: str) -> None:
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
        set_={
            "name": stmt.excluded.name,
            "status": stmt.excluded.status,
            "currency": stmt.excluded.currency,
            "type": stmt.excluded.type,
            "is_test": stmt.excluded.is_test,
            "fetched_at": stmt.excluded.fetched_at,
        },
    )
    session.exec(stmt)


def _upsert_campaign(
    session: Session, account_id: int, camp: dict, now: str,
) -> None:
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
        "fetched_at": now,
    }
    update_cols = {k: getattr(insert(Campaign).values(**values).excluded, k)
                   for k in values if k != "id"}
    stmt = insert(Campaign).values(**values)
    stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=update_cols)
    session.exec(stmt)


def _upsert_campaign_daily_metrics(
    session: Session, camp: dict, now: str,
) -> None:
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
            "ctr": day.get("ctr", 0),
            "cpc": day.get("cpc", 0),
            "fetched_at": now,
        }
        stmt = insert(CampaignDailyMetric).values(**values)
        update_cols = {k: stmt.excluded[k] for k in values
                       if k not in ("campaign_id", "date")}
        stmt = stmt.on_conflict_do_update(
            index_elements=["campaign_id", "date"],
            set_=update_cols,
        )
        session.exec(stmt)


def _upsert_creatives(
    session: Session, account_id: int, camp: dict, now: str,
) -> None:
    for cr in camp.get("creatives", []):
        values = {
            "id": cr.get("id", ""),
            "campaign_id": camp["id"],
            "account_id": account_id,
            "intended_status": cr.get("intended_status"),
            "is_serving": cr.get("is_serving", False),
            "content_reference": cr.get("content_reference"),
            "created_at": cr.get("created_at"),
            "last_modified_at": cr.get("last_modified_at"),
            "fetched_at": now,
        }
        stmt = insert(Creative).values(**values)
        update_cols = {k: stmt.excluded[k] for k in values
                       if k not in ("id", "created_at")}
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_=update_cols,
        )
        session.exec(stmt)


def _upsert_demographics(
    session: Session, acct: dict, date_range: dict, now: str,
) -> None:
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
            update_cols = {k: stmt.excluded[k] for k in values
                           if k not in ("account_id", "pivot_type", "segment", "date_start")}
            stmt = stmt.on_conflict_do_update(
                index_elements=["account_id", "pivot_type", "segment", "date_start"],
                set_=update_cols,
            )
            session.exec(stmt)


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

def table_counts(db_path: Path | None = None) -> dict[str, int]:
    """Return row counts for every table in the database."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    tables = [
        "ad_accounts",
        "campaigns",
        "creatives",
        "campaign_daily_metrics",
        "creative_daily_metrics",
        "audience_demographics",
    ]
    counts = {}
    for t in tables:
        counts[t] = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    conn.close()
    return counts


def active_campaign_audit(db_path: Path | None = None) -> list[dict]:
    """Return active campaigns with potential settings issues."""
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute(
        """SELECT name, status, offsite_delivery_enabled, audience_expansion_enabled,
                  cost_type, daily_budget
           FROM campaigns WHERE status = 'ACTIVE'"""
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        issues = []
        if r["offsite_delivery_enabled"]:
            issues.append("LAN enabled")
        if r["audience_expansion_enabled"]:
            issues.append("Audience Expansion ON")
        if r["cost_type"] == "CPM":
            issues.append("Maximum Delivery (CPM)")
        results.append({"name": r["name"], "issues": issues})
    return results
