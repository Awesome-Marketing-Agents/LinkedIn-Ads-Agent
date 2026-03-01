import { createFileRoute } from "@tanstack/react-router";
import { useState, useMemo } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { CalendarIcon } from "lucide-react";
import { format, subDays, parseISO, isWithinInterval } from "date-fns";
import type { DateRange } from "react-day-picker";
import { useVisualData } from "@/hooks/useReport";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatBlock, StatBlockSkeleton } from "@/components/charts/StatBlock";
import {
  ChartCard,
  ChartCardSkeleton,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  CHART_COLORS,
  CHART_PALETTE,
  type ChartConfig,
} from "@/components/charts/ChartCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer } from "@/components/ui/chart";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";


export const Route = createFileRoute("/visual")({
  component: VisualPage,
});

const presets = [
  { label: "Last 7d", days: 7 },
  { label: "Last 30d", days: 30 },
  { label: "Last 90d", days: 90 },
  { label: "All time", days: 0 },
] as const;

const lineChartConfig = {
  impressions: { label: "Impressions", color: CHART_COLORS.blue },
  clicks: { label: "Clicks", color: CHART_COLORS.teal },
} satisfies ChartConfig;

const barChartConfig = {
  spend: { label: "Spend ($)", color: CHART_COLORS.blue },
} satisfies ChartConfig;

function VisualPage() {
  const { data, isLoading } = useVisualData();
  const [dateRange, setDateRange] = useState<DateRange | undefined>();
  const [popoverOpen, setPopoverOpen] = useState(false);

  const timeSeries = data?.time_series ?? [];
  const campaignComparison = data?.campaign_comparison ?? [];

  const filteredTimeSeries = useMemo(() => {
    if (!dateRange?.from) return timeSeries;
    const from = dateRange.from;
    const to = dateRange.to ?? dateRange.from;
    return timeSeries.filter((r) => {
      const d = parseISO(r.date);
      return isWithinInterval(d, { start: from, end: to });
    });
  }, [timeSeries, dateRange]);

  const kpis = useMemo(() => {
    if (!dateRange?.from) {
      return data?.kpis ?? { impressions: 0, clicks: 0, spend: 0, ctr: 0, cpc: 0, cpm: 0, conversions: 0 };
    }
    const ts = filteredTimeSeries;
    const impressions = ts.reduce((a, r) => a + r.impressions, 0);
    const clicks = ts.reduce((a, r) => a + r.clicks, 0);
    const spend = ts.reduce((a, r) => a + r.spend, 0);
    const ctr = impressions > 0 ? (clicks / impressions) * 100 : 0;
    const cpc = clicks > 0 ? spend / clicks : 0;
    const cpm = impressions > 0 ? (spend / impressions) * 1000 : 0;
    return { impressions, clicks, spend, ctr, cpc, cpm, conversions: 0 };
  }, [data?.kpis, filteredTimeSeries, dateRange]);

  const applyPreset = (days: number) => {
    if (days === 0) {
      setDateRange(undefined);
    } else {
      const to = new Date();
      const from = subDays(to, days);
      setDateRange({ from, to });
    }
    setPopoverOpen(false);
  };

  const pieConfig = useMemo(() => {
    const config: ChartConfig = {};
    campaignComparison.forEach((c, i) => {
      config[c.name] = { label: c.name, color: CHART_PALETTE[i % CHART_PALETTE.length]! };
    });
    return config;
  }, [campaignComparison]);

  if (isLoading) {
    return (
      <>
        <PageHeader title="Performance" />
        <div className="p-6 max-w-6xl">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <StatBlockSkeleton key={i} />
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <ChartCardSkeleton />
            <ChartCardSkeleton />
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader title="Performance">
        <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm" className="text-[12px] gap-1.5">
              <CalendarIcon className="h-3.5 w-3.5" />
              {dateRange?.from ? (
                dateRange.to ? (
                  `${format(dateRange.from, "MMM d")} - ${format(dateRange.to, "MMM d")}`
                ) : (
                  format(dateRange.from, "MMM d, yyyy")
                )
              ) : (
                "All time"
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="end">
            <div className="flex gap-1 p-2 border-b border-border">
              {presets.map((p) => (
                <Button
                  key={p.label}
                  variant="ghost"
                  size="xs"
                  onClick={() => applyPreset(p.days)}
                >
                  {p.label}
                </Button>
              ))}
            </div>
            <Calendar
              mode="range"
              selected={dateRange}
              onSelect={(range) => {
                setDateRange(range);
                if (range?.from && range?.to) setPopoverOpen(false);
              }}
              numberOfMonths={2}
              initialFocus
            />
          </PopoverContent>
        </Popover>
      </PageHeader>

      <div className="p-6 max-w-6xl">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-5">
          <StatBlock label="Impressions" value={kpis.impressions.toLocaleString()} />
          <StatBlock label="Clicks" value={kpis.clicks.toLocaleString()} />
          <StatBlock label="Spend" value={`$${kpis.spend.toFixed(2)}`} />
          <StatBlock label="CTR" value={`${kpis.ctr.toFixed(2)}%`} />
          <StatBlock label="CPC" value={`$${kpis.cpc.toFixed(2)}`} />
          <StatBlock label="CPM" value={`$${kpis.cpm.toFixed(2)}`} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <ChartCard title="Impressions & Clicks" config={lineChartConfig}>
            <LineChart data={filteredTimeSeries} accessibilityLayer>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tickFormatter={(v: string) => v.slice(5)}
              />
              <YAxis yAxisId="left" tickLine={false} axisLine={false} tickMargin={8} />
              <YAxis yAxisId="right" orientation="right" tickLine={false} axisLine={false} tickMargin={8} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <ChartLegend content={<ChartLegendContent />} />
              <Line
                yAxisId="left"
                dataKey="impressions"
                type="monotone"
                stroke="var(--color-impressions)"
                strokeWidth={2}
                dot={false}
              />
              <Line
                yAxisId="right"
                dataKey="clicks"
                type="monotone"
                stroke="var(--color-clicks)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ChartCard>

          <ChartCard title="Daily Spend" config={barChartConfig}>
            <BarChart data={filteredTimeSeries} accessibilityLayer>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                tickFormatter={(v: string) => v.slice(5)}
              />
              <YAxis tickLine={false} axisLine={false} tickMargin={8} />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="spend" fill="var(--color-spend)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ChartCard>
        </div>

        {campaignComparison.length > 0 && (
          <div className="mt-3">
            <Card>
              <CardHeader className="pb-0">
                <CardTitle className="text-[13px]">Spend by Campaign</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col lg:flex-row items-center gap-6">
                  <ChartContainer
                    config={pieConfig}
                    className="aspect-square h-[260px] w-[260px] shrink-0"
                  >
                    <PieChart accessibilityLayer>
                      <ChartTooltip
                        content={
                          <ChartTooltipContent
                            nameKey="name"
                            formatter={(value) => `$${Number(value).toFixed(2)}`}
                          />
                        }
                      />
                      <Pie
                        data={campaignComparison}
                        dataKey="spend"
                        nameKey="name"
                        innerRadius={55}
                        outerRadius={100}
                        strokeWidth={2}
                        stroke="var(--color-background)"
                      >
                        {campaignComparison.map((_, i) => (
                          <Cell
                            key={i}
                            fill={CHART_PALETTE[i % CHART_PALETTE.length]}
                          />
                        ))}
                      </Pie>
                    </PieChart>
                  </ChartContainer>
                  <div className="flex-1 min-w-0 grid grid-cols-1 gap-1 max-h-[260px] overflow-y-auto w-full">
                    {campaignComparison.map((c, i) => {
                      const totalSpend = campaignComparison.reduce((a, x) => a + x.spend, 0);
                      const pct = totalSpend > 0 ? ((c.spend / totalSpend) * 100).toFixed(1) : "0";
                      return (
                        <div key={i} className="flex items-center gap-2 text-[12px] min-w-0">
                          <div
                            className="h-2.5 w-2.5 shrink-0 rounded-sm"
                            style={{ backgroundColor: CHART_PALETTE[i % CHART_PALETTE.length] }}
                          />
                          <span className="truncate text-foreground flex-1 min-w-0">{c.name}</span>
                          <span className="tabular-nums text-muted-foreground shrink-0">
                            ${c.spend.toFixed(2)}
                          </span>
                          <span className="tabular-nums text-muted-foreground/60 shrink-0 w-10 text-right">
                            {pct}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </>
  );
}
