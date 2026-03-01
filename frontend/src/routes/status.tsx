import { createFileRoute } from "@tanstack/react-router";
import { useStatus } from "@/hooks/useReport";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/status")({
  component: StatusPage,
});

function StatusPage() {
  const { data, isLoading } = useStatus();

  if (isLoading) {
    return (
      <>
        <header className="sticky top-0 z-40 flex h-12 items-center border-b border-border bg-background/80 backdrop-blur-sm px-6">
          <h2 className="text-[13px] font-semibold">System</h2>
        </header>
        <div className="p-6">
          <div className="text-[13px] text-muted-foreground">Loading system status...</div>
        </div>
      </>
    );
  }

  const token = data?.token ?? ({} as Record<string, unknown>);
  const db = data?.database ?? {};
  const audit = data?.active_campaign_audit ?? [];
  const connected = (token as { authenticated?: boolean }).authenticated ?? false;

  return (
    <>
      <header className="sticky top-0 z-40 flex h-12 items-center border-b border-border bg-background/80 backdrop-blur-sm px-6">
        <h2 className="text-[13px] font-semibold">System</h2>
      </header>

      <div className="p-6 max-w-2xl space-y-3">
        {/* Token health */}
        <section className="rounded-lg border border-border bg-card px-4 py-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[13px] font-semibold">Token Health</h3>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-medium",
                connected
                  ? "bg-signal-positive/10 text-signal-positive"
                  : "bg-signal-error/10 text-signal-error",
              )}
            >
              {connected ? "Healthy" : "Disconnected"}
            </span>
          </div>

          {connected ? (
            <div className="grid grid-cols-2 gap-3">
              <TokenStat
                label="Access token"
                value={`${(token as { access_token_days_remaining?: number }).access_token_days_remaining ?? 0}d`}
              />
              {(token as { refresh_token_days_remaining?: number | null })
                .refresh_token_days_remaining != null && (
                <TokenStat
                  label="Refresh token"
                  value={`${(token as { refresh_token_days_remaining?: number }).refresh_token_days_remaining}d`}
                />
              )}
            </div>
          ) : (
            <div className="text-[13px] text-muted-foreground">
              No active token. Visit Connection to authenticate.
            </div>
          )}
        </section>

        {/* Database tables */}
        <section className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="px-4 py-3 border-b border-edge-soft">
            <h3 className="text-[13px] font-semibold">Database</h3>
          </div>
          <table className="w-full">
            <thead>
              <tr>
                <th className="px-4 py-1.5 text-left text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground bg-elevated border-b border-edge-soft">
                  Table
                </th>
                <th className="px-4 py-1.5 text-right text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground bg-elevated border-b border-edge-soft">
                  Rows
                </th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(db).map(([table, count]) => (
                <tr key={table} className="hover:bg-accent-muted/30 transition-colors">
                  <td className="px-4 py-1.5 text-[13px] border-b border-edge-soft/50">
                    {table}
                  </td>
                  <td className="px-4 py-1.5 text-[13px] text-right tabular-nums border-b border-edge-soft/50">
                    {(count as number).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Campaign audit */}
        <section className="rounded-lg border border-border bg-card px-4 py-4">
          <h3 className="text-[13px] font-semibold mb-3">Campaign Audit</h3>
          {audit.length === 0 ? (
            <div className="text-[13px] text-muted-foreground">
              No active campaigns to audit.
            </div>
          ) : (
            <div className="space-y-1.5">
              {audit.map((entry, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-[13px]"
                >
                  <span className="font-medium">{entry.name}</span>
                  {entry.issues.length > 0 ? (
                    <span className="rounded-full bg-signal-warning/10 px-2 py-0.5 text-[10px] font-medium text-signal-warning">
                      {entry.issues.length} issue{entry.issues.length > 1 ? "s" : ""}
                    </span>
                  ) : (
                    <span className="rounded-full bg-signal-positive/10 px-2 py-0.5 text-[10px] font-medium text-signal-positive">
                      OK
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </>
  );
}

function TokenStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-elevated px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
        {label}
      </div>
      <div className="text-lg font-semibold tabular-nums leading-tight mt-0.5">
        {value}
      </div>
    </div>
  );
}
