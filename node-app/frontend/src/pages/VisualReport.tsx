import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { StatBlock } from "../components/StatBlock";
import { ChartCard } from "../components/ChartCard";

export function VisualReport() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getVisualData().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <>
        <header className="topbar"><h2>Visual Dashboard</h2></header>
        <div className="content"><div className="card"><p>Loading...</p></div></div>
      </>
    );
  }

  const kpis = (data?.kpis as Record<string, number>) ?? {};
  const timeSeries = (data?.timeSeries as Array<Record<string, unknown>>) ?? [];
  const campaignComparison = (data?.campaignComparison as Array<Record<string, unknown>>) ?? [];

  const timeLabels = timeSeries.map((r) => String(r.date));
  const impressions = timeSeries.map((r) => r.impressions as number);
  const clicks = timeSeries.map((r) => r.clicks as number);
  const spend = timeSeries.map((r) => r.spend as number);

  return (
    <>
      <header className="topbar"><h2>Visual Dashboard</h2></header>
      <div className="content">
        <div className="stat-row">
          <StatBlock label="Impressions" value={kpis.impressions?.toLocaleString() ?? "0"} />
          <StatBlock label="Clicks" value={kpis.clicks?.toLocaleString() ?? "0"} />
          <StatBlock label="Spend" value={`$${kpis.spend?.toFixed(2) ?? "0.00"}`} />
          <StatBlock label="CTR" value={`${kpis.ctr?.toFixed(2) ?? "0"}%`} />
          <StatBlock label="CPC" value={`$${kpis.cpc?.toFixed(2) ?? "0.00"}`} />
          <StatBlock label="CPM" value={`$${kpis.cpm?.toFixed(2) ?? "0.00"}`} />
        </div>

        <ChartCard
          title="Performance Trends"
          type="line"
          data={{
            labels: timeLabels,
            datasets: [
              {
                label: "Impressions",
                data: impressions,
                borderColor: "#2b6cb0",
                backgroundColor: "rgba(43,108,176,0.1)",
                yAxisID: "y",
              },
              {
                label: "Clicks",
                data: clicks,
                borderColor: "#2d8a6e",
                backgroundColor: "rgba(45,138,110,0.1)",
                yAxisID: "y1",
              },
            ],
          }}
          options={{
            scales: {
              y: { type: "linear", position: "left" },
              y1: { type: "linear", position: "right", grid: { drawOnChartArea: false } },
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
                data: spend,
                backgroundColor: "rgba(43,108,176,0.6)",
              },
            ],
          }}
        />

        {campaignComparison.length > 0 && (
          <ChartCard
            title="Spend by Campaign"
            type="doughnut"
            data={{
              labels: campaignComparison.map((c) => String(c.name)),
              datasets: [
                {
                  data: campaignComparison.map((c) => c.spend as number),
                  backgroundColor: [
                    "#2b6cb0", "#2d8a6e", "#d4940a", "#c4483e",
                    "#6b46c1", "#d69e2e", "#e53e3e", "#38a169",
                  ],
                },
              ],
            }}
            height={350}
          />
        )}
      </div>
    </>
  );
}
