import { useState, useEffect } from "react";
import { api } from "../lib/api";

export function Status() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStatus().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <>
        <header className="topbar"><h2>Status</h2></header>
        <div className="content"><div className="card"><p>Loading...</p></div></div>
      </>
    );
  }

  const token = (data?.token as Record<string, unknown>) ?? {};
  const db = (data?.database as Record<string, number>) ?? {};
  const audit = (data?.active_campaign_audit as Array<{ name: string; issues: string[] }>) ?? [];

  return (
    <>
      <header className="topbar"><h2>System Status</h2></header>
      <div className="content">
        <div className="card">
          <h3>Token Status</h3>
          <p>
            Authenticated:{" "}
            <span className={`badge ${token.authenticated ? "badge-ok" : "badge-err"}`}>
              {token.authenticated ? "Yes" : "No"}
            </span>
          </p>
          {Boolean(token.authenticated) && (
            <>
              <p>Access token: {String(token.access_token_days_remaining ?? "")} days remaining</p>
              {token.refresh_token_days_remaining != null && (
                <p>Refresh token: {String(token.refresh_token_days_remaining ?? "")} days remaining</p>
              )}
            </>
          )}
        </div>

        <div className="card">
          <h3>Database</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Table</th><th style={{ textAlign: "right" }}>Rows</th></tr>
              </thead>
              <tbody>
                {Object.entries(db).map(([table, count]) => (
                  <tr key={table}>
                    <td>{table}</td>
                    <td style={{ textAlign: "right" }}>{count.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h3>Active Campaign Audit</h3>
          {audit.length === 0 ? (
            <p>No active campaigns found.</p>
          ) : (
            audit.map((entry, i) => (
              <p key={i}>
                <strong>{entry.name}</strong>:{" "}
                {entry.issues.length > 0 ? (
                  <span className="badge badge-warn">{entry.issues.join(", ")}</span>
                ) : (
                  <span className="badge badge-ok">No issues</span>
                )}
              </p>
            ))
          )}
        </div>
      </div>
    </>
  );
}
