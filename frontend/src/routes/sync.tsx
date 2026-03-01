import { createFileRoute } from "@tanstack/react-router";
import { useRef, useEffect } from "react";
import { useSync } from "@/hooks/useSync";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/sync")({
  component: SyncPage,
});

function SyncPage() {
  const { syncing, logs, done, startSync } = useSync();
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const hasError = logs.some((l) => l.step === "error");

  return (
    <>
      <header className="sticky top-0 z-40 flex h-12 items-center border-b border-border bg-background/80 backdrop-blur-sm px-6">
        <h2 className="text-[13px] font-semibold">Sync</h2>
      </header>

      <div className="p-6 max-w-2xl">
        <div className="rounded-lg border border-border bg-card px-4 py-4 mb-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[13px] font-semibold">Data Synchronization</div>
              <div className="text-[11px] text-muted-foreground mt-0.5">
                Pulls accounts, campaigns, creatives, metrics, and demographics in parallel.
              </div>
            </div>
            <button
              onClick={startSync}
              disabled={syncing}
              className={cn(
                "rounded-md px-3.5 py-1.5 text-[13px] font-medium transition-opacity shrink-0",
                syncing
                  ? "bg-accent-muted text-muted-foreground cursor-wait"
                  : "bg-primary text-primary-foreground hover:opacity-90",
              )}
            >
              {syncing ? "Running..." : "Start Sync"}
            </button>
          </div>
        </div>

        {/* Log output — terminal aesthetic: monospace, dark inset, dense lines */}
        {logs.length > 0 && (
          <div className="rounded-lg border border-border bg-card overflow-hidden mb-3">
            <div className="px-4 py-2 border-b border-edge-soft">
              <span className="text-[11px] font-medium text-muted-foreground">
                Output
              </span>
            </div>
            <div className="bg-background p-3 max-h-[360px] overflow-y-auto font-mono text-[12px] leading-[1.6]">
              {logs.map((log, i) => (
                <div key={i} className="flex gap-2">
                  <span
                    className={cn(
                      "shrink-0 select-none",
                      log.step === "error"
                        ? "text-signal-error"
                        : log.step === "done"
                          ? "text-signal-positive"
                          : "text-ink-faint",
                    )}
                  >
                    {log.step === "error" ? "ERR" : log.step === "done" ? " OK" : "  >"}
                  </span>
                  <span className="text-foreground">{log.detail}</span>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </div>
        )}

        {done && (
          <div
            className={cn(
              "rounded-md border px-4 py-2.5 text-[13px] font-medium",
              hasError
                ? "border-signal-error/20 bg-signal-error/5 text-signal-error"
                : "border-signal-positive/20 bg-signal-positive/5 text-signal-positive",
            )}
          >
            {hasError ? "Sync failed. Review output above." : "Sync complete."}
          </div>
        )}
      </div>
    </>
  );
}
