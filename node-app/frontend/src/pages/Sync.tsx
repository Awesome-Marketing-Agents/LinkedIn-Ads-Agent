import { useState, useRef } from "react";
import { api } from "../lib/api";

interface LogEntry {
  step: string;
  detail: string;
  timestamp: number;
}

export function Sync() {
  const [syncing, setSyncing] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [done, setDone] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  const startSync = async () => {
    setSyncing(true);
    setLogs([]);
    setDone(false);

    const { jobId } = await api.startSync();

    const eventSource = new EventSource(`/api/sync/${jobId}/stream`);
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data) as LogEntry;
      setLogs((prev) => [...prev, data]);

      if (data.step === "done" || data.step === "error") {
        eventSource.close();
        setSyncing(false);
        setDone(true);
      }

      logEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    eventSource.onerror = () => {
      eventSource.close();
      setSyncing(false);
      setDone(true);
    };
  };

  return (
    <>
      <header className="topbar"><h2>Sync Data</h2></header>
      <div className="content">
        <div className="card">
          <h3>Data Synchronization</h3>
          <p>Pull the latest campaigns, creatives, and performance metrics from LinkedIn.</p>
          <p style={{ fontSize: "11px", color: "var(--ink-muted)", marginTop: "var(--sp-2)" }}>
            Metrics, demographics, and creatives are fetched in parallel for faster sync.
          </p>
          <button
            className="btn"
            onClick={startSync}
            disabled={syncing}
            style={{ marginTop: "var(--sp-4)" }}
          >
            {syncing ? "Syncing..." : "Start Sync"}
          </button>
        </div>

        {logs.length > 0 && (
          <div className="card">
            <h3>Sync Progress</h3>
            <pre style={{
              background: "var(--ink)", color: "#e2e8f0",
              padding: "var(--sp-4)", borderRadius: "var(--radius-md)",
              maxHeight: 400, overflowY: "auto", marginTop: "var(--sp-3)",
              fontFamily: "'JetBrains Mono', monospace", fontSize: 12, lineHeight: 1.6,
            }}>
              {logs.map((log, i) => (
                <div key={i}>
                  <span style={{ color: log.step === "error" ? "#fc8181" : "#68d391" }}>
                    [{log.step}]
                  </span>{" "}
                  {log.detail}
                </div>
              ))}
              <div ref={logEndRef} />
            </pre>
          </div>
        )}

        {done && (
          <div className={logs.some((l) => l.step === "error") ? "errbox" : "card"}>
            <p>{logs.some((l) => l.step === "error") ? "Sync failed. Check logs above." : "Sync completed successfully!"}</p>
          </div>
        )}
      </div>
    </>
  );
}
