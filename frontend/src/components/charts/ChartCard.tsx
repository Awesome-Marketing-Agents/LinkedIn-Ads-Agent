import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart";
import { Skeleton } from "@/components/ui/skeleton";

export const CHART_COLORS = {
  blue: "var(--color-chart-1)",
  teal: "var(--color-chart-2)",
  amber: "var(--color-chart-3)",
  rose: "var(--color-chart-4)",
  violet: "var(--color-chart-5)",
  green: "var(--color-chart-6)",
} as const;

export const CHART_PALETTE = Object.values(CHART_COLORS);

interface ChartCardProps {
  title: string;
  config: ChartConfig;
  children: React.ReactElement;
  className?: string;
  containerClassName?: string;
  action?: React.ReactNode;
}

export function ChartCard({
  title,
  config,
  children,
  className,
  containerClassName,
  action,
}: ChartCardProps) {
  return (
    <Card className={className}>
      <CardHeader className="pb-0">
        <div className="flex items-center justify-between">
          <CardTitle className="text-[13px]">{title}</CardTitle>
          {action}
        </div>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={config}
          className={containerClassName ?? "aspect-auto h-[280px] w-full"}
        >
          {children}
        </ChartContainer>
      </CardContent>
    </Card>
  );
}

export function ChartCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-0">
        <Skeleton className="h-4 w-32" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-[280px] w-full" />
      </CardContent>
    </Card>
  );
}

export { ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent };
export type { ChartConfig };
