import { createFileRoute } from "@tanstack/react-router";
import { useVisualData } from "@/hooks/useReport";
import { StatBlock } from "@/components/charts/StatBlock";
import { ChartCard, CHART_COLORS } from "@/components/charts/ChartCard";

export const Route = createFileRoute("/visual")({
  component: VisualPage,
});

function VisualPage() {
  const { data, isLoading } = useVisualData();

  if (isLoading) {
    return (
      <>
        <header className="sticky top-0 z-40 flex h-12 items-center border-b border-border bg-background/80 backdrop-blur-sm px-6">
          <h2 className="text-[13px] font-semibold">Performance</h2>
        </header>
        <div className="p-6">
          <div className="text-[13px] text-muted-foreground">Loading metrics...</div>
        </div>
      </>
    );
  }

  const kpis = data?.kpis ?? {
    impressions: 0,
    clicks: 0,
    spend: 0,
    ctr: 0,
    cpc: 0,
    cpm: 0,
    conversions: 0,
  };
  const timeSeries = data?.time_series ?? [];
  const campaignComparison = data?.campaign_comparison ?? [];

  const timeLabels = timeSeries.map((r) => r.date);

  return (
    <>
      <header className="sticky top-0 z-40 flex h-12 items-center border-b border-border bg-background/80 backdrop-blur-sm px-6">
        <h2 className="text-[13px] font-semibold">Performance</h2>
      </header>

      <div className="p-6 max-w-6xl">
        {/* KPI strip — numbers-first, dense, scannable */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-5">
          <StatBlock
            label="Impressions"
            value={kpis.impressions.toLocaleString()}
          />
          <StatBlock label="Clicks" value={kpis.clicks.toLocaleString()} />
          <StatBlock label="Spend" value={`$${kpis.spend.toFixed(2)}`} />
          <StatBlock label="CTR" value={`${kpis.ctr.toFixed(2)}%`} />
          <StatBlock label="CPC" value={`$${kpis.cpc.toFixed(2)}`} />
          <StatBlock label="CPM" value={`$${kpis.cpm.toFixed(2)}`} />
        </div>

        {/* Charts — system palette, not random hex */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <ChartCard
            title="Impressions & Clicks"
            type="line"
            data={{
              labels: timeLabels,
              datasets: [
                {
                  label: "Impressions",
                  data: timeSeries.map((r) => r.impressions),
                  borderColor: CHART_COLORS.blue,
                  backgroundColor: CHART_COLORS.blue + "18",
                  borderWidth: 1.5,
                  pointRadius: 0,
                  fill: true,
                  tension: 0.3,
                  yAxisID: "y",
                },
                {
                  label: "Clicks",
                  data: timeSeries.map((r) => r.clicks),
                  borderColor: CHART_COLORS.teal,
                  backgroundColor: CHART_COLORS.teal + "18",
                  borderWidth: 1.5,
                  pointRadius: 0,
                  fill: true,
                  tension: 0.3,
                  yAxisID: "y1",
                },
              ],
            }}
            options={{
              interaction: { mode: "index" as const, intersect: false },
              scales: {
                y: {
                  type: "linear" as const,
                  position: "left" as const,
                  grid: { display: false },
                },
                y1: {
                  type: "linear" as const,
                  position: "right" as const,
                  grid: { drawOnChartArea: false },
                },
              },
            }}
          />

          <ChartCard
            title="Daily Spend"
            type="bar"
            data={{
              labels: timeLabels,
              datasets: [
                {
                  label: "Spend ($)",
                  data: timeSeries.map((r) => r.spend),
                  backgroundColor: CHART_COLORS.blue + "80",
                  borderColor: CHART_COLORS.blue,
                  borderWidth: 1,
                  borderRadius: 2,
                },
              ],
            }}
            options={{
              scales: {
                y: { grid: { display: false } },
              },
            }}
          />
        </div>

        {campaignComparison.length > 0 && (
          <div className="mt-3">
            <ChartCard
              title="Spend by Campaign"
              type="doughnut"
              data={{
                labels: campaignComparison.map((c) => c.name),
                datasets: [
                  {
                    data: campaignComparison.map((c) => c.spend),
                    backgroundColor: [
                      CHART_COLORS.blue,
                      CHART_COLORS.teal,
                      CHART_COLORS.amber,
                      CHART_COLORS.rose,
                      CHART_COLORS.violet,
                      CHART_COLORS.green,
                    ],
                    borderWidth: 0,
                  },
                ],
              }}
              options={{
                cutout: "60%",
              } as never}
              height={260}
            />
          </div>
        )}
      </div>
    </>
  );
}
