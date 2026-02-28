import { useRef, useEffect } from "react";
import { Chart, registerables } from "chart.js";

Chart.register(...registerables);

interface ChartCardProps {
  title: string;
  type: "line" | "bar" | "doughnut" | "radar";
  data: Record<string, unknown>;
  options?: Record<string, unknown>;
  height?: number;
}

export function ChartCard({ title, type, data, options = {}, height = 300 }: ChartCardProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    if (chartRef.current) {
      chartRef.current.destroy();
    }

    chartRef.current = new Chart(canvasRef.current, {
      type,
      data: data as any,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        ...options,
      } as any,
    });

    return () => {
      chartRef.current?.destroy();
    };
  }, [type, data, options]);

  return (
    <div className="card">
      <h3>{title}</h3>
      <div style={{ height, marginTop: "var(--sp-3)" }}>
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
}
