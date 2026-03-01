import { useState, useCallback, useRef } from "react";
import type { SyncProgress } from "@/types";
import { createLogger } from "@/lib/logger";

const logger = createLogger("useSync");

export function useSync() {
  const [syncing, setSyncing] = useState(false);
  const [logs, setLogs] = useState<SyncProgress[]>([]);
  const [done, setDone] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const startSync = useCallback(async () => {
    setSyncing(true);
    setLogs([]);
    setDone(false);
    logger.info("Starting sync");

    const res = await fetch("/api/v1/sync", { method: "POST" });
    const { job_id } = await res.json();

    const eventSource = new EventSource(`/api/v1/sync/${job_id}/stream`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data) as SyncProgress;
      setLogs((prev) => [...prev, data]);

      if (data.step === "done" || data.step === "error") {
        eventSource.close();
        setSyncing(false);
        setDone(true);
        logger.info("Sync finished", { step: data.step });
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setSyncing(false);
      setDone(true);
      logger.error("SSE connection error");
    };
  }, []);

  return { syncing, logs, done, startSync };
}
