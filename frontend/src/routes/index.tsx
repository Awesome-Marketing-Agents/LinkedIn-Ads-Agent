import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { KeyRound, RefreshCw, BarChart3, Activity } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { StatusData, TokenStatus } from "@/types";

export const Route = createFileRoute("/")({
  component: Dashboard,
});

function Dashboard() {
  const { data: status, isLoading: statusLoading } = useQuery<StatusData>({
    queryKey: ["status"],
    queryFn: async () => {
      const res = await fetch("/api/v1/status");
      return res.json();
    },
    retry: false,
  });

  const { data: auth, isLoading: authLoading } = useQuery<TokenStatus>({
    queryKey: ["auth", "status"],
    queryFn: async () => {
      const res = await fetch("/api/v1/auth/status");
      return res.json();
    },
    retry: false,
  });

  const isLoading = statusLoading || authLoading;
  const db = status?.database ?? {};
  const connected = auth?.authenticated ?? false;
  const totalRows = Object.values(db).reduce((a, b) => a + (b as number), 0);

  if (isLoading) {
    return (
      <>
        <PageHeader title="Overview" />
        <div className="p-6 max-w-5xl">
          <div className="grid grid-cols-3 gap-3 mb-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <Card key={i} className="py-3">
                <CardContent className="px-4 py-0 space-y-2">
                  <Skeleton className="h-3 w-20" />
                  <Skeleton className="h-5 w-24" />
                  <Skeleton className="h-3 w-32" />
                </CardContent>
              </Card>
            ))}
          </div>
          <Skeleton className="h-3 w-16 mb-3" />
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full mb-1.5" />
          ))}
        </div>
      </>
    );
  }

  const workflow = [
    {
      to: "/auth",
      icon: KeyRound,
      label: "Connection",
      desc: "Link your LinkedIn account via OAuth",
      status: connected ? "complete" : "action-needed",
    },
    {
      to: "/sync",
      icon: RefreshCw,
      label: "Sync",
      desc: "Pull campaigns, creatives, and metrics",
      status: totalRows > 0 ? "complete" : connected ? "ready" : "blocked",
    },
    {
      to: "/visual",
      icon: BarChart3,
      label: "Performance",
      desc: "Charts and KPIs across all campaigns",
      status: totalRows > 0 ? "ready" : "blocked",
    },
    {
      to: "/status",
      icon: Activity,
      label: "System",
      desc: "Token health, database state, campaign audit",
      status: "ready" as const,
    },
  ];

  return (
    <>
      <PageHeader title="Overview" />
      <div className="p-6 max-w-5xl">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
          <Card className="py-3">
            <CardContent className="px-4 py-0">
              <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground mb-1">
                Connection
              </div>
              <div className="flex items-center gap-2">
                <div
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    connected ? "bg-signal-positive" : "bg-signal-error",
                  )}
                />
                <span className="text-[13px] font-medium">
                  {connected ? "Active" : "Disconnected"}
                </span>
              </div>
              {connected && auth?.access_token_days_remaining != null && (
                <div className="text-[11px] text-muted-foreground mt-1 tabular-nums">
                  {auth.access_token_days_remaining}d until token expiry
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="py-3">
            <CardContent className="px-4 py-0">
              <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground mb-1">
                Data Volume
              </div>
              <div className="text-lg font-semibold tabular-nums leading-none">
                {totalRows.toLocaleString()}
              </div>
              <div className="text-[11px] text-muted-foreground mt-1">
                rows across {Object.keys(db).length} tables
              </div>
            </CardContent>
          </Card>

          <Card className="py-3">
            <CardContent className="px-4 py-0">
              <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground mb-1">
                Campaigns
              </div>
              <div className="text-lg font-semibold tabular-nums leading-none">
                {(db.campaigns as number) ?? 0}
              </div>
              <div className="text-[11px] text-muted-foreground mt-1">
                {(db.ad_accounts as number) ?? 0} accounts synced
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground mb-2">
          Workflow
        </div>
        <div className="space-y-1.5">
          {workflow.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="flex items-center gap-3 group"
            >
              <Card className="w-full py-3 hover:bg-accent-muted/50 transition-colors">
                <CardContent className="px-4 py-0 flex items-center gap-3">
                  <item.icon className="h-4 w-4 text-muted-foreground shrink-0 group-hover:text-primary transition-colors" />
                  <div className="flex-1 min-w-0">
                    <div className="text-[13px] font-medium">{item.label}</div>
                    <div className="text-[11px] text-muted-foreground">{item.desc}</div>
                  </div>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div>
                        <StatusBadge status={item.status} />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="text-xs">{statusTooltip(item.status)}</p>
                    </TooltipContent>
                  </Tooltip>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}

function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, { className: string; label: string }> = {
    complete: { className: "border-signal-positive/30 bg-signal-positive/10 text-signal-positive", label: "Done" },
    "action-needed": { className: "border-signal-warning/30 bg-signal-warning/10 text-signal-warning", label: "Required" },
    ready: { className: "border-border bg-accent-muted text-muted-foreground", label: "Ready" },
    blocked: { className: "border-transparent bg-transparent text-muted-foreground/50", label: "Blocked" },
  };
  const v = variants[status] ?? variants.ready!;
  return (
    <Badge variant="outline" className={cn("text-[10px]", v.className)}>
      {v.label}
    </Badge>
  );
}

function statusTooltip(status: string): string {
  const map: Record<string, string> = {
    complete: "This step is complete",
    "action-needed": "Action required to continue",
    ready: "Ready to use",
    blocked: "Complete previous steps first",
  };
  return map[status] ?? "";
}
