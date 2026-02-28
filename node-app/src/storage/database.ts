/**
 * SQLite database connection and initialization.
 *
 * Uses better-sqlite3 for synchronous, high-performance SQLite access
 * with Drizzle ORM for type-safe queries.
 */

import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { DATABASE_FILE } from "../config.js";
import * as schema from "./schema.js";

// Raw SQL schema for initialization (matches Python database.py exactly)
const SCHEMA_SQL = `
CREATE TABLE IF NOT EXISTS ad_accounts (
    id              INTEGER PRIMARY KEY,
    name            TEXT,
    status          TEXT,
    currency        TEXT,
    type            TEXT,
    is_test         BOOLEAN,
    fetched_at      TEXT
);

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
`;

let _db: ReturnType<typeof drizzle> | null = null;
let _sqlite: Database.Database | null = null;

export function getConnection(dbPath?: string): Database.Database {
  const path = dbPath ?? DATABASE_FILE;
  const sqlite = new Database(path);
  sqlite.pragma("journal_mode = WAL");
  sqlite.exec(SCHEMA_SQL);
  return sqlite;
}

export function getDb(dbPath?: string): ReturnType<typeof drizzle<typeof schema>> {
  if (!_db) {
    _sqlite = getConnection(dbPath);
    _db = drizzle(_sqlite, { schema });
  }
  return _db as ReturnType<typeof drizzle<typeof schema>>;
}

export function closeDb(): void {
  if (_sqlite) {
    _sqlite.close();
    _sqlite = null;
    _db = null;
  }
}
