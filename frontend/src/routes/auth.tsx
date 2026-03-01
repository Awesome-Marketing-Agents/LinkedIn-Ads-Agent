import { createFileRoute } from "@tanstack/react-router";
import { useAuthStatus, useStartAuth } from "@/hooks/useAuth";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/auth")({
  component: AuthPage,
});

function AuthPage() {
  const { data: status, isLoading } = useAuthStatus();
  const startAuth = useStartAuth();

  const connected = status?.authenticated ?? false;

  return (
    <>
      <PageHeader title="Connection" />
      <div className="p-6 max-w-xl">
        {isLoading ? (
          <Card>
            <CardHeader>
              <Skeleton className="h-4 w-32" />
            </CardHeader>
            <CardContent className="space-y-3">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-2 w-full" />
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-2 w-full" />
            </CardContent>
          </Card>
        ) : connected ? (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-[13px]">LinkedIn OAuth</CardTitle>
                <Badge variant="outline" className="border-signal-positive/30 bg-signal-positive/10 text-signal-positive">
                  Connected
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <TokenRow
                label="Access token"
                days={status!.access_token_days_remaining ?? 0}
                maxDays={60}
              />
              {status!.refresh_token_days_remaining != null && (
                <TokenRow
                  label="Refresh token"
                  days={status!.refresh_token_days_remaining}
                  maxDays={365}
                />
              )}
              {status!.saved_at && (
                <div className="text-[11px] text-muted-foreground pt-3 border-t border-edge-soft">
                  Token saved {status!.saved_at}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-[13px]">Connect LinkedIn</CardTitle>
                <Badge variant="outline" className="border-signal-error/30 bg-signal-error/10 text-signal-error">
                  Disconnected
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-[13px] text-muted-foreground mb-4">
                Authorize this app to read your ad account data via LinkedIn's Marketing API.
              </p>
              <Button onClick={startAuth}>
                Authorize with LinkedIn
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </>
  );
}

function TokenRow({
  label,
  days,
  maxDays,
}: {
  label: string;
  days: number;
  maxDays: number;
}) {
  const pct = Math.max(0, Math.min(100, (days / maxDays) * 100));
  const urgent = days < 7;

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[11px] text-muted-foreground">{label}</span>
        <span
          className={cn(
            "text-[11px] font-medium tabular-nums",
            urgent ? "text-signal-warning" : "text-foreground",
          )}
        >
          {days}d remaining
        </span>
      </div>
      <Progress
        value={pct}
        className={cn("h-1.5", urgent && "[&>div]:bg-signal-warning")}
      />
    </div>
  );
}
