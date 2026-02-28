/**
 * Data-access layer: upsert and query helpers for the LinkedIn Ads SQLite DB.
 *
 * The public API is persistSnapshot(snapshotDict) which writes an entire
 * assembled snapshot into the normalised tables using INSERT OR REPLACE.
 */

import { getConnection } from "./database.js";
import { logger } from "../logger.js";
import { StorageError } from "../errors.js";

interface SnapshotAccount {
  id: number;
  name: string;
  status: string;
  currency?: string;
  type?: string;
  test?: boolean;
  campaigns?: SnapshotCampaign[];
  audience_demographics?: Record<string, SnapshotDemoSegment[]>;
}

interface SnapshotCampaign {
  id: number;
  name: string;
  status: string;
  type?: string;
  settings?: Record<string, unknown>;
  daily_metrics?: SnapshotDailyMetric[];
  creatives?: SnapshotCreative[];
}

interface SnapshotDailyMetric {
  date: string;
  impressions?: number;
  clicks?: number;
  spend?: number;
  landing_page_clicks?: number;
  conversions?: number;
  likes?: number;
  comments?: number;
  shares?: number;
  ctr?: number;
  cpc?: number;
}

interface SnapshotCreative {
  id?: string;
  intended_status?: string;
  is_serving?: boolean;
  content_reference?: string;
  created_at?: number;
  last_modified_at?: number;
}

interface SnapshotDemoSegment {
  segment?: string;
  impressions?: number;
  clicks?: number;
  ctr?: number;
  share_of_impressions?: number;
}

interface Snapshot {
  accounts?: SnapshotAccount[];
  date_range?: { start?: string; end?: string };
}

export function persistSnapshot(snap: Snapshot, dbPath?: string): void {
  try {
    const conn = getConnection(dbPath);
    const now = new Date().toISOString();

    const upsertAccount = conn.prepare(`
      INSERT OR REPLACE INTO ad_accounts
      (id, name, status, currency, type, is_test, fetched_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    const upsertCampaign = conn.prepare(`
      INSERT OR REPLACE INTO campaigns
      (id, account_id, name, status, type, daily_budget,
       daily_budget_currency, total_budget, cost_type, unit_cost,
       bid_strategy, creative_selection, offsite_delivery_enabled,
       audience_expansion_enabled, campaign_group, fetched_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    `);

    const upsertMetric = conn.prepare(`
      INSERT OR REPLACE INTO campaign_daily_metrics
      (campaign_id, date, impressions, clicks, spend,
       landing_page_clicks, conversions, likes, comments,
       shares, ctr, cpc, fetched_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    `);

    const upsertCreative = conn.prepare(`
      INSERT OR REPLACE INTO creatives
      (id, campaign_id, account_id, intended_status, is_serving,
       content_reference, created_at, last_modified_at, fetched_at)
      VALUES (?,?,?,?,?,?,?,?,?)
    `);

    const upsertDemo = conn.prepare(`
      INSERT OR REPLACE INTO audience_demographics
      (account_id, pivot_type, segment, impressions, clicks,
       ctr, share_pct, date_start, date_end, fetched_at)
      VALUES (?,?,?,?,?,?,?,?,?,?)
    `);

    const dateRange = snap.date_range ?? {};

    // Use a transaction for atomicity and performance
    const insertAll = conn.transaction(() => {
      for (const acct of snap.accounts ?? []) {
        upsertAccount.run(
          acct.id,
          acct.name,
          acct.status,
          acct.currency ?? null,
          acct.type ?? null,
          acct.test ? 1 : 0,
          now,
        );

        for (const camp of acct.campaigns ?? []) {
          const s = camp.settings ?? {};
          upsertCampaign.run(
            camp.id,
            acct.id,
            camp.name,
            camp.status,
            camp.type ?? null,
            parseFloat(String(s.daily_budget ?? 0)),
            s.daily_budget_currency ?? null,
            parseFloat(String(s.total_budget ?? 0)),
            s.cost_type ?? null,
            parseFloat(String(s.unit_cost ?? 0)),
            s.bid_strategy ?? null,
            s.creative_selection ?? null,
            s.offsite_delivery_enabled ? 1 : 0,
            s.audience_expansion_enabled ? 1 : 0,
            s.campaign_group ?? null,
            now,
          );

          for (const day of camp.daily_metrics ?? []) {
            upsertMetric.run(
              camp.id,
              day.date,
              day.impressions ?? 0,
              day.clicks ?? 0,
              day.spend ?? 0,
              day.landing_page_clicks ?? 0,
              day.conversions ?? 0,
              day.likes ?? 0,
              day.comments ?? 0,
              day.shares ?? 0,
              day.ctr ?? 0,
              day.cpc ?? 0,
              now,
            );
          }

          for (const cr of camp.creatives ?? []) {
            upsertCreative.run(
              cr.id ?? "",
              camp.id,
              acct.id,
              cr.intended_status ?? null,
              cr.is_serving ? 1 : 0,
              cr.content_reference ?? null,
              cr.created_at ?? null,
              cr.last_modified_at ?? null,
              now,
            );
          }
        }

        // Demographics
        for (const [pivotType, segments] of Object.entries(
          acct.audience_demographics ?? {},
        )) {
          for (const seg of segments) {
            upsertDemo.run(
              acct.id,
              pivotType,
              seg.segment ?? "?",
              seg.impressions ?? 0,
              seg.clicks ?? 0,
              seg.ctr ?? 0,
              seg.share_of_impressions ?? 0,
              dateRange.start ?? "",
              dateRange.end ?? "",
              now,
            );
          }
        }
      }
    });

    insertAll();
    conn.close();
  } catch (e) {
    logger.error(`Database error while persisting snapshot: ${e}`);
    throw new StorageError(
      "Failed to persist snapshot to database",
      "persist_snapshot",
      "multiple",
    );
  }
}

export function tableCounts(dbPath?: string): Record<string, number> {
  const conn = getConnection(dbPath);
  const tables = [
    "ad_accounts",
    "campaigns",
    "creatives",
    "campaign_daily_metrics",
    "creative_daily_metrics",
    "audience_demographics",
  ];
  const counts: Record<string, number> = {};
  for (const t of tables) {
    const row = conn.prepare(`SELECT COUNT(*) as cnt FROM ${t}`).get() as {
      cnt: number;
    };
    counts[t] = row.cnt;
  }
  conn.close();
  return counts;
}

export function activeCampaignAudit(
  dbPath?: string,
): Array<{ name: string; issues: string[] }> {
  const conn = getConnection(dbPath);
  const rows = conn
    .prepare(
      `SELECT name, status, offsite_delivery_enabled, audience_expansion_enabled,
              cost_type, daily_budget
       FROM campaigns WHERE status = 'ACTIVE'`,
    )
    .all() as Array<{
    name: string;
    offsite_delivery_enabled: number;
    audience_expansion_enabled: number;
    cost_type: string;
    daily_budget: number;
  }>;
  conn.close();

  return rows.map((r) => {
    const issues: string[] = [];
    if (r.offsite_delivery_enabled) issues.push("LAN enabled");
    if (r.audience_expansion_enabled) issues.push("Audience Expansion ON");
    if (r.cost_type === "CPM") issues.push("Maximum Delivery (CPM)");
    return { name: r.name, issues };
  });
}
