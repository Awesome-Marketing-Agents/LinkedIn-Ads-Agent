import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { DataTable } from "../components/DataTable";

type Mode = "campaign_daily" | "creative_daily" | "demographics";

const modes: { key: Mode; label: string }[] = [
  { key: "campaign_daily", label: "Campaign Metrics" },
  { key: "creative_daily", label: "Creative Metrics" },
  { key: "demographics", label: "Demographics" },
];

const campaignColumns = [
  { key: "campaign_name", label: "Campaign" },
  { key: "date", label: "Date" },
  { key: "impressions", label: "Impressions", align: "right" as const },
  { key: "clicks", label: "Clicks", align: "right" as const },
  { key: "spend", label: "Spend", align: "right" as const },
  { key: "ctr", label: "CTR %", align: "right" as const },
  { key: "cpc", label: "CPC", align: "right" as const },
];

const creativeColumns = [
  { key: "creative_id", label: "Creative ID" },
  { key: "date", label: "Date" },
  { key: "impressions", label: "Impressions", align: "right" as const },
  { key: "clicks", label: "Clicks", align: "right" as const },
  { key: "spend", label: "Spend", align: "right" as const },
  { key: "ctr", label: "CTR %", align: "right" as const },
];

const demoColumns = [
  { key: "pivot_type", label: "Pivot" },
  { key: "segment", label: "Segment" },
  { key: "impressions", label: "Impressions", align: "right" as const },
  { key: "clicks", label: "Clicks", align: "right" as const },
  { key: "ctr", label: "CTR %", align: "right" as const },
  { key: "share_pct", label: "Share %", align: "right" as const },
];

export function Report() {
  const [mode, setMode] = useState<Mode>("campaign_daily");
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    let fetcher: Promise<Record<string, unknown>>;

    if (mode === "campaign_daily") {
      fetcher = api.getCampaignMetrics(page);
    } else if (mode === "creative_daily") {
      fetcher = api.getCreativeMetrics(page);
    } else {
      fetcher = api.getDemographics();
    }

    fetcher
      .then((data) => {
        setRows((data.rows as Record<string, unknown>[]) ?? []);
        setTotalPages((data.totalPages as number) ?? 1);
      })
      .finally(() => setLoading(false));
  }, [mode, page]);

  const columns =
    mode === "campaign_daily"
      ? campaignColumns
      : mode === "creative_daily"
        ? creativeColumns
        : demoColumns;

  return (
    <>
      <header className="topbar"><h2>Report Tables</h2></header>
      <div className="content">
        <div className="card">
          <div style={{ display: "flex", gap: "var(--sp-2)", marginBottom: "var(--sp-4)" }}>
            {modes.map((m) => (
              <button
                key={m.key}
                className={`btn ${mode === m.key ? "" : "btn-ghost"}`}
                onClick={() => { setMode(m.key); setPage(1); }}
                style={mode !== m.key ? { background: "transparent", color: "var(--ink-secondary)", border: "1px solid var(--border-strong)" } : {}}
              >
                {m.label}
              </button>
            ))}
          </div>

          {loading ? (
            <p>Loading...</p>
          ) : (
            <DataTable
              columns={columns}
              rows={rows}
              page={mode !== "demographics" ? page : undefined}
              totalPages={mode !== "demographics" ? totalPages : undefined}
              onPageChange={mode !== "demographics" ? setPage : undefined}
            />
          )}
        </div>
      </div>
    </>
  );
}
