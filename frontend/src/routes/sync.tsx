import { createFileRoute } from "@tanstack/react-router";
import { useRef, useEffect } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useSync } from "@/hooks/useSync";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/sync")({
  component: SyncPage,
});

function SyncPage() {
  const { syncing, logs, done, startSync } = useSync();
  const logEndRef = useRef<HTMLDivElement>(null);
  const toastFired = useRef(false);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    if (done && !toastFired.current) {
      toastFired.current = true;
      const hasError = logs.some((l) => l.step === "error");
      if (hasError) {
        toast.error("Sync failed. Review output above.");
      } else {
        toast.success("Sync complete.");
      }
    }
    if (!done) {
      toastFired.current = false;
    }
  }, [done, logs]);

  const hasError = logs.some((l) => l.step === "error");

  return (
    <>
      <PageHeader title="Sync" />
      <div className="p-6 max-w-2xl">
        <Card className="mb-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-[13px]">Data Synchronization</CardTitle>
                <CardDescription className="text-[11px] mt-0.5">
                  Pulls accounts, campaigns, creatives, metrics, and demographics in parallel.
                </CardDescription>
              </div>
              <Button onClick={startSync} disabled={syncing} className="shrink-0">
                {syncing && <Loader2 className="h-4 w-4 animate-spin" />}
                {syncing ? "Running..." : "Start Sync"}
              </Button>
            </div>
          </CardHeader>
        </Card>

        {logs.length > 0 && (
          <Card className="mb-3 overflow-hidden">
            <CardHeader className="py-2 px-4 border-b border-edge-soft">
              <span className="text-[11px] font-medium text-muted-foreground">Output</span>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[360px]">
                <div className="p-3 font-mono text-[12px] leading-[1.6]">
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
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {done && (
          <Alert variant={hasError ? "destructive" : "default"} className={cn(!hasError && "border-signal-positive/30 bg-signal-positive/5 text-signal-positive")}>
            <AlertDescription className="text-[13px] font-medium">
              {hasError ? "Sync failed. Review output above." : "Sync complete."}
            </AlertDescription>
          </Alert>
        )}
      </div>
    </>
  );
}
