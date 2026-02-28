/**
 * Report API routes - serves data for the React frontend.
 */

import type { FastifyInstance } from "fastify";
import { getConnection } from "../storage/database.js";

export async function reportRoutes(fastify: FastifyInstance): Promise<void> {
  // Campaign daily metrics with pagination
  fastify.get("/api/report/campaign-metrics", async (request) => {
    const query = request.query as Record<string, string>;
    const page = parseInt(query.page ?? "1", 10);
    const pageSize = parseInt(query.pageSize ?? "50", 10);
    const offset = (page - 1) * pageSize;

    const conn = getConnection();

    const total = (
      conn.prepare("SELECT COUNT(*) as cnt FROM campaign_daily_metrics").get() as {
        cnt: number;
      }
    ).cnt;

    const rows = conn
      .prepare(
        `SELECT cdm.*, c.name as campaign_name
         FROM campaign_daily_metrics cdm
         LEFT JOIN campaigns c ON cdm.campaign_id = c.id
         ORDER BY cdm.date DESC, cdm.campaign_id
         LIMIT ? OFFSET ?`,
      )
      .all(pageSize, offset);

    conn.close();
    return { rows, total, page, pageSize, totalPages: Math.ceil(total / pageSize) };
  });

  // Creative daily metrics
  fastify.get("/api/report/creative-metrics", async (request) => {
    const query = request.query as Record<string, string>;
    const page = parseInt(query.page ?? "1", 10);
    const pageSize = parseInt(query.pageSize ?? "50", 10);
    const offset = (page - 1) * pageSize;

    const conn = getConnection();

    const total = (
      conn.prepare("SELECT COUNT(*) as cnt FROM creative_daily_metrics").get() as {
        cnt: number;
      }
    ).cnt;

    const rows = conn
      .prepare(
        `SELECT * FROM creative_daily_metrics
         ORDER BY date DESC, creative_id
         LIMIT ? OFFSET ?`,
      )
      .all(pageSize, offset);

    conn.close();
    return { rows, total, page, pageSize, totalPages: Math.ceil(total / pageSize) };
  });

  // Demographics
  fastify.get("/api/report/demographics", async (request) => {
    const query = request.query as Record<string, string>;
    const pivotType = query.pivot_type;

    const conn = getConnection();

    let rows;
    if (pivotType) {
      rows = conn
        .prepare(
          `SELECT * FROM audience_demographics WHERE pivot_type = ? ORDER BY impressions DESC`,
        )
        .all(pivotType);
    } else {
      rows = conn
        .prepare(
          `SELECT * FROM audience_demographics ORDER BY pivot_type, impressions DESC`,
        )
        .all();
    }

    conn.close();
    return { rows };
  });

  // Visual dashboard data (for charts)
  fastify.get("/api/report/visual", async () => {
    const conn = getConnection();

    // Time series data
    const timeSeries = conn
      .prepare(
        `SELECT date, SUM(impressions) as impressions, SUM(clicks) as clicks,
                SUM(spend) as spend, SUM(conversions) as conversions
         FROM campaign_daily_metrics
         GROUP BY date ORDER BY date`,
      )
      .all();

    // Campaign comparison
    const campaignComparison = conn
      .prepare(
        `SELECT c.name, SUM(cdm.impressions) as impressions, SUM(cdm.clicks) as clicks,
                SUM(cdm.spend) as spend, SUM(cdm.conversions) as conversions
         FROM campaign_daily_metrics cdm
         JOIN campaigns c ON cdm.campaign_id = c.id
         GROUP BY cdm.campaign_id
         ORDER BY SUM(cdm.spend) DESC`,
      )
      .all();

    // Summary KPIs
    const summary = conn
      .prepare(
        `SELECT SUM(impressions) as total_impressions, SUM(clicks) as total_clicks,
                SUM(spend) as total_spend, SUM(conversions) as total_conversions
         FROM campaign_daily_metrics`,
      )
      .get() as Record<string, number>;

    conn.close();

    const totalImp = summary?.total_impressions ?? 0;
    const totalClk = summary?.total_clicks ?? 0;
    const totalSpend = summary?.total_spend ?? 0;
    const totalConv = summary?.total_conversions ?? 0;

    return {
      timeSeries,
      campaignComparison,
      kpis: {
        impressions: totalImp,
        clicks: totalClk,
        spend: Number(totalSpend.toFixed(2)),
        conversions: totalConv,
        ctr: totalImp ? Number(((totalClk / totalImp) * 100).toFixed(4)) : 0,
        cpc: totalClk ? Number((totalSpend / totalClk).toFixed(2)) : 0,
        cpm: totalImp ? Number(((totalSpend / totalImp) * 1000).toFixed(2)) : 0,
      },
    };
  });

  // Campaigns list
  fastify.get("/api/report/campaigns", async () => {
    const conn = getConnection();
    const rows = conn
      .prepare(
        `SELECT c.*, a.name as account_name
         FROM campaigns c
         LEFT JOIN ad_accounts a ON c.account_id = a.id
         ORDER BY c.status, c.name`,
      )
      .all();
    conn.close();
    return { rows };
  });

  // Accounts
  fastify.get("/api/report/accounts", async () => {
    const conn = getConnection();
    const rows = conn
      .prepare("SELECT * FROM ad_accounts ORDER BY name")
      .all();
    conn.close();
    return { rows };
  });
}
