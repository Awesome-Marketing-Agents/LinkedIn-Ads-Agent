import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { DataTable } from "@/components/tables/DataTable";
import { cn } from "@/lib/utils";

type Mode = "campaign_daily" | "creative_daily" | "demographics";

const tabs: { key: Mode; label: string }[] = [
  { key: "campaign_daily", label: "Campaigns" },
  { key: "creative_daily", label: "Creatives" },
  { key: "demographics", label: "Demographics" },
];

const campaignColumns = [
  { key: "campaign_name", label: "Campaign" },
  { key: "date", label: "Date" },
  { key: "impressions", label: "Impr.", align: "right" as const },
  { key: "clicks", label: "Clicks", align: "right" as const },
  { key: "spend", label: "Spend", align: "right" as const },
  { key: "ctr", label: "CTR", align: "right" as const },
  { key: "cpc", label: "CPC", align: "right" as const },
];

const creativeColumns = [
  { key: "creative_id", label: "Creative" },
  { key: "date", label: "Date" },
  { key: "impressions", label: "Impr.", align: "right" as const },
  { key: "clicks", label: "Clicks", align: "right" as const },
  { key: "spend", label: "Spend", align: "right" as const },
  { key: "ctr", label: "CTR", align: "right" as const },
];

const demoColumns = [
  { key: "pivot_type", label: "Pivot" },
  { key: "segment", label: "Segment" },
  { key: "impressions", label: "Impr.", align: "right" as const },
  { key: "clicks", label: "Clicks", align: "right" as const },
  { key: "ctr", label: "CTR", align: "right" as const },
  { key: "share_pct", label: "Share %", align: "right" as const },
];

export const Route = createFileRoute("/report")({
  component: ReportPage,
});

function ReportPage() {
  const [mode, setMode] = useState<Mode>("campaign_daily");
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    let url: string;

    if (mode === "campaign_daily") {
      url = `/api/v1/report/campaign-metrics?page=${page}&page_size=50`;
    } else if (mode === "creative_daily") {
      url = `/api/v1/report/creative-metrics?page=${page}&page_size=50`;
    } else {
      url = "/api/v1/report/demographics";
    }

    fetch(url)
      .then((r) => r.json())
      .then((data) => {
        setRows((data.rows as Record<string, unknown>[]) ?? []);
        setTotalPages((data.total_pages as number) ?? 1);
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
      <header className="sticky top-0 z-40 flex h-12 items-center border-b border-border bg-background/80 backdrop-blur-sm px-6">
        <h2 className="text-[13px] font-semibold">Tables</h2>
      </header>

      <div className="p-6">
        {/* Tab bar — underline style, not button pills */}
        <div className="flex gap-4 border-b border-border mb-4">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => {
                setMode(t.key);
                setPage(1);
              }}
              className={cn(
                "pb-2 text-[13px] font-medium border-b-2 transition-colors -mb-px",
                mode === t.key
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground",
              )}
            >
              {t.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-[13px] text-muted-foreground py-8">Loading...</div>
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
    </>
  );
}
