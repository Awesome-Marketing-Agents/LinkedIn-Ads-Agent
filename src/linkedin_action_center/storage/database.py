"""SQLite schema initialisation and connection helper.

Defines all tables used by the LinkedIn Ads Action Center and provides:

- ``get_connection()`` — raw ``sqlite3.Connection`` (legacy, still used)
- ``get_engine()``     — SQLAlchemy ``Engine`` singleton
- ``get_session()``    — SQLModel ``Session`` context-manager
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from linkedin_action_center.core.config import DATABASE_FILE, settings

_SCHEMA = """\
-- Ad accounts
CREATE TABLE IF NOT EXISTS ad_accounts (
    id              INTEGER PRIMARY KEY,
    name            TEXT,
    status          TEXT,
    currency        TEXT,
    type            TEXT,
    is_test         BOOLEAN,
    created_at      TEXT,
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
    created_at                  TEXT,
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

-- Sync run log (freshness gate)
CREATE TABLE IF NOT EXISTS sync_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id          TEXT    NOT NULL,
    started_at          TEXT    NOT NULL,
    finished_at         TEXT,
    status              TEXT    NOT NULL DEFAULT 'running',
    trigger             TEXT,
    campaigns_fetched   INTEGER DEFAULT 0,
    creatives_fetched   INTEGER DEFAULT 0,
    api_calls_made      INTEGER DEFAULT 0,
    errors              TEXT
);
"""


# ---------------------------------------------------------------------------
# Legacy raw sqlite3 interface
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# SQLAlchemy / SQLModel interface
# ---------------------------------------------------------------------------

_engine = None


def get_engine(db_url: str | None = None):
    """Return a (cached) SQLAlchemy Engine for the application database."""
    global _engine
    if _engine is None or db_url is not None:
        url = db_url or settings.database_url
        _engine = create_engine(url, echo=False)

        # Enable WAL mode on every new SQLite connection
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return _engine


@contextmanager
def get_session(db_url: str | None = None) -> Generator[Session, None, None]:
    """Yield a SQLModel ``Session`` bound to the application engine."""
    engine = get_engine(db_url)
    with Session(engine) as session:
        yield session
