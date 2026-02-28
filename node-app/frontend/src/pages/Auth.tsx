import { useState, useEffect } from "react";
import { api } from "../lib/api";

export function Auth() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAuthStatus().then(setStatus).finally(() => setLoading(false));
  }, []);

  const handleAuth = async () => {
    const { url } = await api.getAuthUrl();
    window.location.href = url;
  };

  return (
    <>
      <header className="topbar"><h2>Authentication</h2></header>
      <div className="content">
        {loading ? (
          <div className="card"><p>Loading...</p></div>
        ) : status?.authenticated ? (
          <div className="card">
            <h3>Authenticated</h3>
            <p>
              <span className="badge badge-ok">Connected</span>
            </p>
            <p>Access token: {String(status.access_token_days_remaining ?? "")} days remaining</p>
            {status.refresh_token_days_remaining != null && (
              <p>Refresh token: {String(status.refresh_token_days_remaining ?? "")} days remaining</p>
            )}
            {status.saved_at != null && <p style={{ fontSize: "11px", color: "var(--ink-muted)" }}>Last saved: {String(status.saved_at ?? "")}</p>}
          </div>
        ) : (
          <div className="card">
            <h3>Not Authenticated</h3>
            <p>Connect your LinkedIn account to start pulling ad data.</p>
            <button className="btn" onClick={handleAuth} style={{ marginTop: "var(--sp-3)" }}>
              Connect LinkedIn Account
            </button>
          </div>
        )}
      </div>
    </>
  );
}
