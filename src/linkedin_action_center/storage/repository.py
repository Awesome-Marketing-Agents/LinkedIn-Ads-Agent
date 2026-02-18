"""Data-access layer: upsert and query helpers for the LinkedIn Ads SQLite DB.

The public API is ``persist_snapshot(snapshot_dict)`` which writes an entire
assembled snapshot into the normalised tables using INSERT OR REPLACE.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from linkedin_action_center.storage.database import get_connection


def persist_snapshot(snap: dict, db_path: Path | None = None) -> None:
    """Write the full snapshot dict into SQLite (upsert pattern)."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now(tz=timezone.utc).isoformat()

    for acct in snap.get("accounts", []):
        _upsert_account(cur, acct, now)

        for camp in acct.get("campaigns", []):
            _upsert_campaign(cur, acct["id"], camp, now)
            _upsert_campaign_daily_metrics(cur, camp, now)
            _upsert_creatives(cur, acct["id"], camp, now)

        _upsert_demographics(cur, acct, snap.get("date_range", {}), now)

    conn.commit()
    conn.close()


# Private upsert helpers

def _upsert_account(cur: sqlite3.Cursor, acct: dict, now: str) -> None:
    cur.execute(
        """INSERT OR REPLACE INTO ad_accounts
           (id, name, status, currency, type, is_test, fetched_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            acct["id"],
            acct["name"],
            acct["status"],
            acct.get("currency"),
            acct.get("type"),
            acct.get("test", False),
            now,
        ),
    )


def _upsert_campaign(
    cur: sqlite3.Cursor, account_id: int, camp: dict, now: str,
) -> None:
    s = camp.get("settings", {})
    cur.execute(
        """INSERT OR REPLACE INTO campaigns
           (id, account_id, name, status, type, daily_budget,
            daily_budget_currency, total_budget, cost_type, unit_cost,
            bid_strategy, creative_selection, offsite_delivery_enabled,
            audience_expansion_enabled, campaign_group, fetched_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            camp["id"],
            account_id,
            camp["name"],
            camp["status"],
            camp.get("type"),
            float(s.get("daily_budget") or 0),
            s.get("daily_budget_currency"),
            float(s.get("total_budget") or 0),
            s.get("cost_type"),
            float(s.get("unit_cost") or 0),
            s.get("bid_strategy"),
            s.get("creative_selection"),
            s.get("offsite_delivery_enabled", False),
            s.get("audience_expansion_enabled", False),
            s.get("campaign_group"),
            now,
        ),
    )


def _upsert_campaign_daily_metrics(
    cur: sqlite3.Cursor, camp: dict, now: str,
) -> None:
    for day in camp.get("daily_metrics", []):
        cur.execute(
            """INSERT OR REPLACE INTO campaign_daily_metrics
               (campaign_id, date, impressions, clicks, spend,
                landing_page_clicks, conversions, likes, comments,
                shares, ctr, cpc, fetched_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                camp["id"],
                day["date"],
                day.get("impressions", 0),
                day.get("clicks", 0),
                day.get("spend", 0),
                day.get("landing_page_clicks", 0),
                day.get("conversions", 0),
                day.get("likes", 0),
                day.get("comments", 0),
                day.get("shares", 0),
                day.get("ctr", 0),
                day.get("cpc", 0),
                now,
            ),
        )


def _upsert_creatives(
    cur: sqlite3.Cursor, account_id: int, camp: dict, now: str,
) -> None:
    for cr in camp.get("creatives", []):
        cur.execute(
            """INSERT OR REPLACE INTO creatives
               (id, campaign_id, account_id, intended_status, is_serving,
                content_reference, created_at, last_modified_at, fetched_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                cr.get("id", ""),
                camp["id"],
                account_id,
                cr.get("intended_status"),
                cr.get("is_serving", False),
                cr.get("content_reference"),
                cr.get("created_at"),
                cr.get("last_modified_at"),
                now,
            ),
        )


def _upsert_demographics(
    cur: sqlite3.Cursor, acct: dict, date_range: dict, now: str,
) -> None:
    for pivot_type, segments in acct.get("audience_demographics", {}).items():
        for seg in segments:
            cur.execute(
                """INSERT OR REPLACE INTO audience_demographics
                   (account_id, pivot_type, segment, impressions, clicks,
                    ctr, share_pct, date_start, date_end, fetched_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    acct["id"],
                    pivot_type,
                    seg.get("segment", "?"),
                    seg.get("impressions", 0),
                    seg.get("clicks", 0),
                    seg.get("ctr", 0),
                    seg.get("share_of_impressions", 0),
                    date_range.get("start", ""),
                    date_range.get("end", ""),
                    now,
                ),
            )


# Read helpers (for verification / future use)

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
