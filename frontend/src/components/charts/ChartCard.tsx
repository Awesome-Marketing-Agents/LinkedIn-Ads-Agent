import { useRef, useEffect } from "react";
import {
  Chart,
  registerables,
  type ChartData,
  type ChartOptions,
  type ChartType,
} from "chart.js";

Chart.register(...registerables);

/* Chart.js defaults tuned for the design system */
Chart.defaults.color = "oklch(0.48 0.012 250)"; /* ink-faint */
Chart.defaults.borderColor = "oklch(0.26 0.012 250 / 0.4)"; /* edge, subtle */
Chart.defaults.font.family = "Inter, system-ui, sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend!.labels!.boxWidth = 10;
Chart.defaults.plugins.legend!.labels!.boxHeight = 10;
Chart.defaults.plugins.legend!.labels!.padding = 16;

/* Palette — desaturated, professional, readable on dark backgrounds */
export const CHART_COLORS = {
  blue: "oklch(0.62 0.12 240)",
  teal: "oklch(0.65 0.12 185)",
  amber: "oklch(0.72 0.14 75)",
  rose: "oklch(0.65 0.14 15)",
  violet: "oklch(0.58 0.12 290)",
  green: "oklch(0.65 0.12 155)",
} as const;

export const CHART_PALETTE = Object.values(CHART_COLORS);

interface ChartCardProps {
  title: string;
  type: ChartType;
  data: ChartData;
  options?: ChartOptions;
  height?: number;
}

export function ChartCard({
  title,
  type,
  data,
  options = {},
  height = 280,
}: ChartCardProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    chartRef.current?.destroy();

    chartRef.current = new Chart(canvasRef.current, {
      type,
      data: data as never,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300, easing: "easeOutQuart" },
        plugins: {
          legend: {
            position: "bottom" as const,
            labels: { usePointStyle: true, pointStyle: "circle" },
          },
        },
        ...options,
      } as never,
    });

    return () => {
      chartRef.current?.destroy();
    };
  }, [type, data, options]);

  return (
    <div className="rounded-lg border border-border bg-card p-5 mb-3">
      <h3 className="text-[13px] font-semibold text-card-foreground mb-4">
        {title}
      </h3>
      <div style={{ height }}>
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
}
