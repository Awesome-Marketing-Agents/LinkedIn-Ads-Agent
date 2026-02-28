/**
 * Snapshot assembly: transform raw API data into a structured dict for analysis.
 *
 * Also handles writing the snapshot to JSON on disk.
 *
 * Line-by-line port of the Python snapshot.py with identical output format.
 */

import fs from "node:fs";
import path from "node:path";
import { SNAPSHOT_DIR } from "../config.js";

// -- Internal helpers --------------------------------------------------------

function extractIdFromUrn(urn: string): string {
  const s = String(urn);
  return s.includes(":") ? s.split(":").pop()! : s;
}

interface AggregatedMetrics {
  impressions: number;
  clicks: number;
  spend: number;
  landing_page_clicks: number;
  conversions: number;
  likes: number;
  comments: number;
  shares: number;
  follows: number;
  leads: number;
  opens: number;
  sends: number;
  ctr: number;
  cpc: number;
  cpm: number;
  cpl: number;
}

function aggregateMetrics(rows: Record<string, unknown>[]): AggregatedMetrics {
  const agg = {
    impressions: 0,
    clicks: 0,
    spend: 0,
    landing_page_clicks: 0,
    conversions: 0,
    likes: 0,
    comments: 0,
    shares: 0,
    follows: 0,
    leads: 0,
    opens: 0,
    sends: 0,
    ctr: 0,
    cpc: 0,
    cpm: 0,
    cpl: 0,
  };

  for (const r of rows) {
    agg.impressions += (r.impressions as number) ?? 0;
    agg.clicks += (r.clicks as number) ?? 0;
    agg.spend += parseFloat(String(r.costInLocalCurrency ?? "0") || "0");
    agg.landing_page_clicks += (r.landingPageClicks as number) ?? 0;
    agg.conversions += (r.externalWebsiteConversions as number) ?? 0;
    agg.likes += (r.likes as number) ?? 0;
    agg.comments += (r.comments as number) ?? 0;
    agg.shares += (r.shares as number) ?? 0;
    agg.follows += (r.follows as number) ?? 0;
    agg.leads += (r.oneClickLeads as number) ?? 0;
    agg.opens += (r.opens as number) ?? 0;
    agg.sends += (r.sends as number) ?? 0;
  }

  const { impressions: imp, clicks: clk, spend, conversions: conv } = agg;

  agg.ctr = imp ? Number((clk / imp * 100).toFixed(4)) : 0;
  agg.cpc = clk ? Number((spend / clk).toFixed(2)) : 0;
  agg.cpm = imp ? Number((spend / imp * 1000).toFixed(2)) : 0;
  agg.cpl = conv ? Number((spend / conv).toFixed(2)) : 0;
  agg.spend = Number(spend.toFixed(2));

  return agg;
}

interface DailyMetric {
  date: string;
  impressions: number;
  clicks: number;
  spend: number;
  landing_page_clicks: number;
  conversions: number;
  likes: number;
  comments: number;
  shares: number;
  follows: number;
  leads: number;
  opens: number;
  sends: number;
  ctr: number;
  cpc: number;
}

function dailyTimeSeries(rows: Record<string, unknown>[]): DailyMetric[] {
  const daily = new Map<string, DailyMetric>();

  for (const r of rows) {
    const dr = (r.dateRange as Record<string, Record<string, number>>) ?? {};
    const start = dr.start ?? {};
    const dateKey = `${start.year ?? 0}-${String(start.month ?? 0).padStart(2, "0")}-${String(start.day ?? 0).padStart(2, "0")}`;

    if (!daily.has(dateKey)) {
      daily.set(dateKey, {
        date: dateKey,
        impressions: 0,
        clicks: 0,
        spend: 0,
        landing_page_clicks: 0,
        conversions: 0,
        likes: 0,
        comments: 0,
        shares: 0,
        follows: 0,
        leads: 0,
        opens: 0,
        sends: 0,
        ctr: 0,
        cpc: 0,
      });
    }

    const d = daily.get(dateKey)!;
    d.impressions += (r.impressions as number) ?? 0;
    d.clicks += (r.clicks as number) ?? 0;
    d.spend += parseFloat(String(r.costInLocalCurrency ?? "0") || "0");
    d.landing_page_clicks += (r.landingPageClicks as number) ?? 0;
    d.conversions += (r.externalWebsiteConversions as number) ?? 0;
    d.likes += (r.likes as number) ?? 0;
    d.comments += (r.comments as number) ?? 0;
    d.shares += (r.shares as number) ?? 0;
    d.follows += (r.follows as number) ?? 0;
    d.leads += (r.oneClickLeads as number) ?? 0;
    d.opens += (r.opens as number) ?? 0;
    d.sends += (r.sends as number) ?? 0;
  }

  const result: DailyMetric[] = [];
  const sorted = [...daily.values()].sort((a, b) =>
    a.date.localeCompare(b.date),
  );

  for (const d of sorted) {
    d.spend = Number(d.spend.toFixed(2));
    d.ctr = d.impressions
      ? Number(((d.clicks / d.impressions) * 100).toFixed(4))
      : 0;
    d.cpc = d.clicks ? Number((d.spend / d.clicks).toFixed(2)) : 0;
    result.push(d);
  }

  return result;
}

// -- Well-known LinkedIn enum lookups ----------------------------------------

const SENIORITY_MAP: Record<string, string> = {
  "1": "Unpaid",
  "2": "Training",
  "3": "Entry",
  "4": "Senior",
  "5": "Manager",
  "6": "Director",
  "7": "VP",
  "8": "CXO",
  "9": "Partner",
  "10": "Owner",
};

const COMPANY_SIZE_MAP: Record<string, string> = {
  A: "Self-employed (1)",
  B: "2–10 employees",
  C: "11–50 employees",
  D: "51–200 employees",
  E: "201–500 employees",
  F: "501–1,000 employees",
  G: "1,001–5,000 employees",
  H: "5,001–10,000 employees",
  I: "10,001+ employees",
};

const JOB_FUNCTION_MAP: Record<string, string> = {
  "1": "Accounting",
  "2": "Administrative",
  "3": "Arts and Design",
  "4": "Business Development",
  "5": "Community & Social Services",
  "6": "Consulting",
  "7": "Education",
  "8": "Engineering",
  "9": "Entrepreneurship",
  "10": "Finance",
  "11": "Healthcare Services",
  "12": "Human Resources",
  "13": "Information Technology",
  "14": "Legal",
  "15": "Marketing",
  "16": "Media & Communications",
  "17": "Military & Protective Services",
  "18": "Operations",
  "19": "Product Management",
  "20": "Program & Project Management",
  "21": "Purchasing",
  "22": "Quality Assurance",
  "23": "Real Estate",
  "24": "Research",
  "25": "Sales",
  "26": "Customer Success & Support",
};

function resolveUrnLocally(urn: string): string {
  const s = String(urn);
  const parts = s.split(":");
  if (parts.length < 4) return "";

  const entityType = parts[2];
  const entityId = parts[3];

  if (entityType === "seniority") return SENIORITY_MAP[entityId] ?? "";
  if (entityType === "companySizeRange" || entityType === "companySize")
    return COMPANY_SIZE_MAP[entityId] ?? "";
  if (entityType === "function") return JOB_FUNCTION_MAP[entityId] ?? "";
  return "";
}

function topDemographics(
  demoRows: Record<string, unknown>[],
  urnNames: Record<string, string> = {},
  topN = 10,
): Record<string, unknown>[] {
  const sortedRows = [...demoRows].sort(
    (a, b) =>
      ((b.impressions as number) ?? 0) - ((a.impressions as number) ?? 0),
  );

  const totalImp = sortedRows.reduce(
    (sum, r) => sum + ((r.impressions as number) ?? 0),
    0,
  );

  return sortedRows.slice(0, topN).map((r) => {
    const imp = (r.impressions as number) ?? 0;
    const clk = (r.clicks as number) ?? 0;
    const rawSegment = ((r.pivotValues as string[]) ?? ["?"])[0];
    const resolvedName =
      urnNames[rawSegment] || resolveUrnLocally(rawSegment);

    return {
      segment: resolvedName || rawSegment,
      segment_urn: rawSegment,
      impressions: imp,
      clicks: clk,
      ctr: imp ? Number(((clk / imp) * 100).toFixed(2)) : 0,
      share_of_impressions: totalImp
        ? Number(((imp / totalImp) * 100).toFixed(1))
        : 0,
    };
  });
}

// -- Public API --------------------------------------------------------------

export function assembleSnapshot(
  accounts: Record<string, unknown>[],
  campaignsList: Record<string, unknown>[],
  creativesList: Record<string, unknown>[],
  campMetrics: Record<string, unknown>[],
  creatMetrics: Record<string, unknown>[],
  demoData: Record<string, unknown>,
  dateStart: Date,
  dateEnd: Date,
): Record<string, unknown> {
  // Index campaign metrics by campaign ID
  const campMetricMap = new Map<string, Record<string, unknown>[]>();
  for (const r of campMetrics) {
    for (const pv of (r.pivotValues as string[]) ?? []) {
      const cid = extractIdFromUrn(pv);
      if (!campMetricMap.has(cid)) campMetricMap.set(cid, []);
      campMetricMap.get(cid)!.push(r);
    }
  }

  // Index creative metrics by creative URN
  const creatMetricMap = new Map<string, Record<string, unknown>[]>();
  for (const r of creatMetrics) {
    for (const pv of (r.pivotValues as string[]) ?? []) {
      if (String(pv).includes("sponsoredCreative")) {
        if (!creatMetricMap.has(pv)) creatMetricMap.set(pv, []);
        creatMetricMap.get(pv)!.push(r);
      }
    }
  }

  // Index creatives by campaign URN
  const creativesByCampaign = new Map<string, Record<string, unknown>[]>();
  for (const cr of creativesList) {
    const campUrn = (cr.campaign as string) ?? "";
    if (!creativesByCampaign.has(campUrn))
      creativesByCampaign.set(campUrn, []);
    creativesByCampaign.get(campUrn)!.push(cr);
  }

  // Index campaigns by account
  const campaignsByAccountId = new Map<number, Record<string, unknown>[]>();
  for (const camp of campaignsList) {
    const acctId = camp._account_id as number | undefined;
    if (acctId == null) continue;
    const acctIdInt = Number(acctId);
    if (isNaN(acctIdInt)) continue;
    if (!campaignsByAccountId.has(acctIdInt))
      campaignsByAccountId.set(acctIdInt, []);
    campaignsByAccountId.get(acctIdInt)!.push(camp);
  }

  const diffDays = Math.floor(
    (dateEnd.getTime() - dateStart.getTime()) / (1000 * 60 * 60 * 24),
  );

  const snapshot: Record<string, unknown> = {
    generated_at: new Date().toISOString(),
    date_range: {
      start: dateStart.toISOString().split("T")[0],
      end: dateEnd.toISOString().split("T")[0],
      days: diffDays,
    },
    accounts: [] as Record<string, unknown>[],
  };

  for (const acct of accounts) {
    const acctSnapshot: Record<string, unknown> = {
      id: acct.id,
      name: acct.name,
      status: acct.status,
      currency: acct.currency,
      type: acct.type,
      test: acct.test ?? false,
      campaigns: [] as Record<string, unknown>[],
      audience_demographics: {} as Record<string, unknown>,
    };

    const acctId = acct.id as number | undefined;
    let acctCampaigns =
      acctId != null ? campaignsByAccountId.get(acctId) : undefined;
    if (!acctCampaigns) {
      // Backwards compatibility
      acctCampaigns = campaignsList;
    }

    for (const camp of acctCampaigns) {
      const campId = String(camp.id ?? "");
      const campUrn = `urn:li:sponsoredCampaign:${campId}`;

      const budget = (camp.dailyBudget as Record<string, unknown>) ?? {};
      const totalBudget = (camp.totalBudget as Record<string, unknown>) ?? {};
      const unitCost = (camp.unitCost as Record<string, unknown>) ?? {};

      const campSnapshot: Record<string, unknown> = {
        id: camp.id,
        name: camp.name,
        status: camp.status,
        type: camp.type,
        settings: {
          daily_budget: budget.amount ?? null,
          daily_budget_currency: budget.currencyCode ?? null,
          total_budget: totalBudget.amount ?? null,
          cost_type: camp.costType,
          unit_cost: unitCost.amount ?? null,
          bid_strategy: camp.optimizationTargetType,
          creative_selection: camp.creativeSelection,
          offsite_delivery_enabled: camp.offsiteDeliveryEnabled ?? false,
          audience_expansion_enabled: camp.audienceExpansionEnabled ?? false,
          run_schedule: camp.runSchedule,
          campaign_group: camp.campaignGroup,
        },
        metrics_summary: {},
        daily_metrics: [] as unknown[],
        creatives: [] as unknown[],
      };

      // Aggregate campaign metrics
      const campRows = campMetricMap.get(campId) ?? [];
      if (campRows.length > 0) {
        campSnapshot.metrics_summary = aggregateMetrics(campRows);
        campSnapshot.daily_metrics = dailyTimeSeries(campRows);
      }

      // Attach creatives and their metrics
      for (const cr of creativesByCampaign.get(campUrn) ?? []) {
        const crId = cr.id as string;
        const crSnapshot: Record<string, unknown> = {
          id: crId,
          intended_status: cr.intendedStatus,
          is_serving: cr.isServing ?? false,
          serving_hold_reasons: cr.servingHoldReasons ?? [],
          content_reference: ((cr.content as Record<string, unknown>) ?? {})
            .reference,
          created_at: cr.createdAt,
          last_modified_at: cr.lastModifiedAt,
          metrics_summary: {},
        };
        const crRows = creatMetricMap.get(crId) ?? [];
        if (crRows.length > 0) {
          crSnapshot.metrics_summary = aggregateMetrics(crRows);
        }
        (campSnapshot.creatives as Record<string, unknown>[]).push(crSnapshot);
      }

      (acctSnapshot.campaigns as Record<string, unknown>[]).push(campSnapshot);
    }

    // Audience demographics
    let acctDemoRaw: Record<string, Record<string, unknown>[]> | null = null;
    let urnNames: Record<string, string> = {};

    if (typeof demoData === "object" && demoData !== null && acctId != null && acctId in demoData) {
      const entry = (demoData as Record<string, unknown>)[acctId as unknown as string] as Record<string, unknown>;
      if (typeof entry === "object" && entry !== null && "pivots" in entry) {
        acctDemoRaw = entry.pivots as Record<string, Record<string, unknown>[]>;
        urnNames = (entry.urn_names as Record<string, string>) ?? {};
      } else if (typeof entry === "object" && entry !== null) {
        acctDemoRaw = entry as Record<string, Record<string, unknown>[]>;
      }
    } else if (typeof demoData === "object" && demoData !== null) {
      acctDemoRaw = demoData as Record<string, Record<string, unknown>[]>;
    }

    if (acctDemoRaw) {
      const demographics: Record<string, unknown> = {};
      for (const [pivot, rows] of Object.entries(acctDemoRaw)) {
        const key = String(pivot).toLowerCase().replace("member_", "");
        demographics[key] = topDemographics(rows ?? [], urnNames);
      }
      acctSnapshot.audience_demographics = demographics;
    }

    (snapshot.accounts as Record<string, unknown>[]).push(acctSnapshot);
  }

  return snapshot;
}

export function saveSnapshotJson(
  snap: Record<string, unknown>,
  filePath?: string,
): string {
  if (!filePath) {
    const ts = new Date()
      .toISOString()
      .replace(/[-:]/g, "")
      .replace("T", "T")
      .split(".")[0] + "Z";
    filePath = path.join(SNAPSHOT_DIR, `snapshot_${ts}.json`);
  }

  const dir = path.dirname(filePath);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(snap, null, 2));
  return filePath;
}
