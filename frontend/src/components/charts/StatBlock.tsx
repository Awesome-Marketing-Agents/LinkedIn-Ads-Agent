import { cn } from "@/lib/utils";

interface StatBlockProps {
  label: string;
  value: string | number;
  meta?: string;
  trend?: { direction: "up" | "down" | "flat"; label: string };
}

export function StatBlock({ label, value, meta, trend }: StatBlockProps) {
  return (
    <div className="flex-1 min-w-[140px] rounded-lg border border-border bg-card px-4 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground mb-1">
        {label}
      </div>
      <div className="text-2xl font-semibold tabular-nums tracking-tight text-card-foreground leading-none">
        {value}
      </div>
      <div className="flex items-center gap-2 mt-1.5 min-h-[16px]">
        {trend && (
          <span
            className={cn(
              "text-[11px] font-medium tabular-nums",
              trend.direction === "up" && "text-signal-positive",
              trend.direction === "down" && "text-signal-error",
              trend.direction === "flat" && "text-muted-foreground",
            )}
          >
            {trend.direction === "up" && "+"}
            {trend.label}
          </span>
        )}
        {meta && (
          <span className="text-[11px] text-muted-foreground">{meta}</span>
        )}
      </div>
    </div>
  );
}
