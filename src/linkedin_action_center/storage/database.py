"""SQLite schema initialisation and connection helper.

Defines all six tables used by the LinkedIn Ads Action Center and provides a
single ``get_connection`` function other modules call to obtain a ready-to-use
``sqlite3.Connection``.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from linkedin_action_center.core.config import DATABASE_FILE

_SCHEMA = """\
-- Ad accounts
CREATE TABLE IF NOT EXISTS ad_accounts (
    id              INTEGER PRIMARY KEY,
    name            TEXT,
    status          TEXT,
    currency        TEXT,
    type            TEXT,
    is_test         BOOLEAN,
    fetched_at      TEXT
);

-- Campaigns with settings
CREATE TABLE IF NOT EXISTS campaigns (
    id                          INTEGER PRIMARY KEY,
    account_id                  INTEGER,
    name                        TEXT,
    status                      TEXT,
    type                        TEXT,
    daily_budget                REAL,
    daily_budget_currency       TEXT,
    total_budget                REAL,
    cost_type                   TEXT,
    unit_cost                   REAL,
    bid_strategy                TEXT,
    creative_selection          TEXT,
    offsite_delivery_enabled    BOOLEAN,
    audience_expansion_enabled  BOOLEAN,
    campaign_group              TEXT,
    fetched_at                  TEXT,
    FOREIGN KEY (account_id) REFERENCES ad_accounts(id)
);

-- Creatives
CREATE TABLE IF NOT EXISTS creatives (
    id                  TEXT PRIMARY KEY,
    campaign_id         INTEGER,
    account_id          INTEGER,
    intended_status     TEXT,
    is_serving          BOOLEAN,
    content_reference   TEXT,
    created_at          INTEGER,
    last_modified_at    INTEGER,
    fetched_at          TEXT,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
    FOREIGN KEY (account_id) REFERENCES ad_accounts(id)
);

-- Daily campaign metrics (time series)
CREATE TABLE IF NOT EXISTS campaign_daily_metrics (
    campaign_id         INTEGER,
    date                TEXT,
    impressions         INTEGER,
    clicks              INTEGER,
    spend               REAL,
    landing_page_clicks INTEGER,
    conversions         INTEGER,
    likes               INTEGER,
    comments            INTEGER,
    shares              INTEGER,
    ctr                 REAL,
    cpc                 REAL,
    fetched_at          TEXT,
    PRIMARY KEY (campaign_id, date),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- Daily creative metrics (time series)
CREATE TABLE IF NOT EXISTS creative_daily_metrics (
    creative_id         TEXT,
    date                TEXT,
    impressions         INTEGER,
    clicks              INTEGER,
    spend               REAL,
    landing_page_clicks INTEGER,
    conversions         INTEGER,
    likes               INTEGER,
    comments            INTEGER,
    shares              INTEGER,
    ctr                 REAL,
    cpc                 REAL,
    fetched_at          TEXT,
    PRIMARY KEY (creative_id, date),
    FOREIGN KEY (creative_id) REFERENCES creatives(id)
);

-- Audience demographics (aggregated)
CREATE TABLE IF NOT EXISTS audience_demographics (
    account_id      INTEGER,
    pivot_type      TEXT,
    segment         TEXT,
    impressions     INTEGER,
    clicks          INTEGER,
    ctr             REAL,
    share_pct       REAL,
    date_start      TEXT,
    date_end        TEXT,
    fetched_at      TEXT,
    PRIMARY KEY (account_id, pivot_type, segment, date_start),
    FOREIGN KEY (account_id) REFERENCES ad_accounts(id)
);
"""


def init_database(db_path: Path | None = None) -> Path:
    """Initialize database schema and return the database path."""
    path = db_path or DATABASE_FILE
    conn = get_connection(path)
    conn.close()
    return path


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Return a connection with WAL journal mode and the schema applied."""
    path = db_path or DATABASE_FILE
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn
