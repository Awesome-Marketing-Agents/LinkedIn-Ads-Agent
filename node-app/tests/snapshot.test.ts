import { describe, it, expect } from "vitest";
import { assembleSnapshot } from "../src/storage/snapshot.js";

describe("assembleSnapshot", () => {
  it("produces correct structure with empty inputs", () => {
    const result = assembleSnapshot([], [], [], [], [], {}, new Date("2025-01-01"), new Date("2025-03-31"));
    expect(result.generated_at).toBeDefined();
    expect(result.date_range).toBeDefined();
    expect((result.date_range as any).days).toBe(89);
    expect(result.accounts).toEqual([]);
  });

  it("correctly aggregates campaign metrics", () => {
    const accounts = [{ id: 1, name: "Test Account", status: "ACTIVE" }];
    const campaigns = [
      { id: 100, name: "Campaign 1", status: "ACTIVE", _account_id: 1 },
    ];
    const campMetrics = [
      {
        impressions: 1000,
        clicks: 50,
        costInLocalCurrency: "25.50",
        landingPageClicks: 30,
        externalWebsiteConversions: 5,
        likes: 10,
        comments: 2,
        shares: 3,
        follows: 1,
        oneClickLeads: 0,
        opens: 0,
        sends: 0,
        pivotValues: ["urn:li:sponsoredCampaign:100"],
        dateRange: { start: { year: 2025, month: 1, day: 15 } },
      },
      {
        impressions: 2000,
        clicks: 100,
        costInLocalCurrency: "50.00",
        landingPageClicks: 60,
        externalWebsiteConversions: 10,
        likes: 20,
        comments: 4,
        shares: 6,
        follows: 2,
        oneClickLeads: 0,
        opens: 0,
        sends: 0,
        pivotValues: ["urn:li:sponsoredCampaign:100"],
        dateRange: { start: { year: 2025, month: 1, day: 16 } },
      },
    ];

    const result = assembleSnapshot(
      accounts,
      campaigns,
      [],
      campMetrics,
      [],
      {},
      new Date("2025-01-01"),
      new Date("2025-03-31"),
    );

    const accts = result.accounts as any[];
    expect(accts).toHaveLength(1);
    expect(accts[0].campaigns).toHaveLength(1);

    const camp = accts[0].campaigns[0];
    expect(camp.metrics_summary.impressions).toBe(3000);
    expect(camp.metrics_summary.clicks).toBe(150);
    expect(camp.metrics_summary.spend).toBe(75.50);
    expect(camp.metrics_summary.ctr).toBeCloseTo(5.0, 1);
    expect(camp.metrics_summary.cpc).toBeCloseTo(0.5, 1);

    expect(camp.daily_metrics).toHaveLength(2);
    expect(camp.daily_metrics[0].date).toBe("2025-01-15");
    expect(camp.daily_metrics[1].date).toBe("2025-01-16");
  });

  it("resolves seniority URNs locally", () => {
    const accounts = [{ id: 1, name: "Test", status: "ACTIVE" }];
    const demoData: Record<string, unknown> = {
      MEMBER_SENIORITY: [
        { impressions: 500, clicks: 25, pivotValues: ["urn:li:seniority:6"] },
        { impressions: 300, clicks: 15, pivotValues: ["urn:li:seniority:8"] },
      ],
    };

    const result = assembleSnapshot(
      accounts,
      [],
      [],
      [],
      [],
      demoData,
      new Date("2025-01-01"),
      new Date("2025-03-31"),
    );

    const acct = (result.accounts as any[])[0];
    const seniority = acct.audience_demographics.seniority;
    expect(seniority).toHaveLength(2);
    expect(seniority[0].segment).toBe("Director");
    expect(seniority[1].segment).toBe("CXO");
  });
});
