import { createFileRoute } from "@tanstack/react-router";
import { useAuthStatus, useStartAuth } from "@/hooks/useAuth";
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
      <header className="sticky top-0 z-40 flex h-12 items-center border-b border-border bg-background/80 backdrop-blur-sm px-6">
        <h2 className="text-[13px] font-semibold">Connection</h2>
      </header>

      <div className="p-6 max-w-xl">
        {isLoading ? (
          <div className="rounded-lg border border-border bg-card px-4 py-6">
            <div className="text-[13px] text-muted-foreground">Loading token status...</div>
          </div>
        ) : connected ? (
          <div className="space-y-3">
            <div className="rounded-lg border border-border bg-card px-4 py-4">
              <div className="flex items-center justify-between mb-3">
                <div className="text-[13px] font-semibold">LinkedIn OAuth</div>
                <span className="rounded-full bg-signal-positive/10 px-2 py-0.5 text-[10px] font-medium text-signal-positive">
                  Connected
                </span>
              </div>

              <div className="space-y-2">
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
              </div>

              {status!.saved_at && (
                <div className="text-[11px] text-muted-foreground mt-3 pt-3 border-t border-edge-soft">
                  Token saved {status!.saved_at}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="rounded-lg border border-border bg-card px-4 py-4">
            <div className="text-[13px] font-semibold mb-1">Connect LinkedIn</div>
            <div className="text-[13px] text-muted-foreground mb-4">
              Authorize this app to read your ad account data via LinkedIn's Marketing API.
            </div>
            <button
              onClick={startAuth}
              className="rounded-md bg-primary px-3.5 py-1.5 text-[13px] font-medium text-primary-foreground hover:opacity-90 transition-opacity"
            >
              Authorize with LinkedIn
            </button>
          </div>
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
      <div className="flex items-center justify-between mb-1">
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
      <div className="h-1 rounded-full bg-edge-soft overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all",
            urgent ? "bg-signal-warning" : "bg-primary",
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
