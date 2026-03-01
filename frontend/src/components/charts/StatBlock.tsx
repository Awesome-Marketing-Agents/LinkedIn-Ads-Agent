import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface StatBlockProps {
  label: string;
  value: string | number;
  meta?: string;
  trend?: { direction: "up" | "down" | "flat"; label: string };
}

export function StatBlock({ label, value, meta, trend }: StatBlockProps) {
  const TrendIcon =
    trend?.direction === "up"
      ? TrendingUp
      : trend?.direction === "down"
        ? TrendingDown
        : Minus;

  return (
    <Card className="py-3 gap-1">
      <CardContent className="px-4 py-0">
        <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground mb-1">
          {label}
        </div>
        <div className="text-2xl font-semibold tabular-nums tracking-tight text-card-foreground leading-none">
          {value}
        </div>
        <div className="flex items-center gap-1.5 mt-1.5 min-h-[16px]">
          {trend && (
            <span
              className={cn(
                "flex items-center gap-1 text-[11px] font-medium tabular-nums",
                trend.direction === "up" && "text-signal-positive",
                trend.direction === "down" && "text-signal-error",
                trend.direction === "flat" && "text-muted-foreground",
              )}
            >
              <TrendIcon className="h-3 w-3" />
              {trend.direction === "up" && "+"}
              {trend.label}
            </span>
          )}
          {meta && (
            <span className="text-[11px] text-muted-foreground">{meta}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function StatBlockSkeleton() {
  return (
    <Card className="py-3 gap-1">
      <CardContent className="px-4 py-0">
        <Skeleton className="h-3 w-16 mb-2" />
        <Skeleton className="h-7 w-24 mb-2" />
        <Skeleton className="h-3 w-20" />
      </CardContent>
    </Card>
  );
}
