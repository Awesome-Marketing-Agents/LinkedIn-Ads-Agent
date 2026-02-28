/**
 * Drizzle ORM schema definitions for all 6 SQLite tables.
 *
 * Mirrors the Python database.py schema exactly.
 */

import {
  sqliteTable,
  text,
  integer,
  real,
  primaryKey,
} from "drizzle-orm/sqlite-core";

export const adAccounts = sqliteTable("ad_accounts", {
  id: integer("id").primaryKey(),
  name: text("name"),
  status: text("status"),
  currency: text("currency"),
  type: text("type"),
  isTest: integer("is_test", { mode: "boolean" }),
  fetchedAt: text("fetched_at"),
});

export const campaigns = sqliteTable("campaigns", {
  id: integer("id").primaryKey(),
  accountId: integer("account_id").references(() => adAccounts.id),
  name: text("name"),
  status: text("status"),
  type: text("type"),
  dailyBudget: real("daily_budget"),
  dailyBudgetCurrency: text("daily_budget_currency"),
  totalBudget: real("total_budget"),
  costType: text("cost_type"),
  unitCost: real("unit_cost"),
  bidStrategy: text("bid_strategy"),
  creativeSelection: text("creative_selection"),
  offsiteDeliveryEnabled: integer("offsite_delivery_enabled", {
    mode: "boolean",
  }),
  audienceExpansionEnabled: integer("audience_expansion_enabled", {
    mode: "boolean",
  }),
  campaignGroup: text("campaign_group"),
  fetchedAt: text("fetched_at"),
});

export const creatives = sqliteTable("creatives", {
  id: text("id").primaryKey(),
  campaignId: integer("campaign_id").references(() => campaigns.id),
  accountId: integer("account_id").references(() => adAccounts.id),
  intendedStatus: text("intended_status"),
  isServing: integer("is_serving", { mode: "boolean" }),
  contentReference: text("content_reference"),
  createdAt: integer("created_at"),
  lastModifiedAt: integer("last_modified_at"),
  fetchedAt: text("fetched_at"),
});

export const campaignDailyMetrics = sqliteTable(
  "campaign_daily_metrics",
  {
    campaignId: integer("campaign_id").references(() => campaigns.id),
    date: text("date"),
    impressions: integer("impressions"),
    clicks: integer("clicks"),
    spend: real("spend"),
    landingPageClicks: integer("landing_page_clicks"),
    conversions: integer("conversions"),
    likes: integer("likes"),
    comments: integer("comments"),
    shares: integer("shares"),
    ctr: real("ctr"),
    cpc: real("cpc"),
    fetchedAt: text("fetched_at"),
  },
  (table) => [primaryKey({ columns: [table.campaignId, table.date] })],
);

export const creativeDailyMetrics = sqliteTable(
  "creative_daily_metrics",
  {
    creativeId: text("creative_id").references(() => creatives.id),
    date: text("date"),
    impressions: integer("impressions"),
    clicks: integer("clicks"),
    spend: real("spend"),
    landingPageClicks: integer("landing_page_clicks"),
    conversions: integer("conversions"),
    likes: integer("likes"),
    comments: integer("comments"),
    shares: integer("shares"),
    ctr: real("ctr"),
    cpc: real("cpc"),
    fetchedAt: text("fetched_at"),
  },
  (table) => [primaryKey({ columns: [table.creativeId, table.date] })],
);

export const audienceDemographics = sqliteTable(
  "audience_demographics",
  {
    accountId: integer("account_id").references(() => adAccounts.id),
    pivotType: text("pivot_type"),
    segment: text("segment"),
    impressions: integer("impressions"),
    clicks: integer("clicks"),
    ctr: real("ctr"),
    sharePct: real("share_pct"),
    dateStart: text("date_start"),
    dateEnd: text("date_end"),
    fetchedAt: text("fetched_at"),
  },
  (table) => [
    primaryKey({
      columns: [table.accountId, table.pivotType, table.segment, table.dateStart],
    }),
  ],
);
