import { Link } from "react-router-dom";

const actions = [
  { step: 1, title: "Authenticate", desc: "Connect your LinkedIn account via OAuth.", to: "/auth" },
  { step: 2, title: "Sync Data", desc: "Pull campaigns, creatives, and metrics from LinkedIn.", to: "/sync" },
  { step: 3, title: "Explore", desc: "View visual charts and tabular reports.", to: "/visual" },
  { step: 4, title: "Status", desc: "Check token health and database status.", to: "/status" },
];

export function Dashboard() {
  return (
    <>
      <header className="topbar"><h2>Dashboard</h2></header>
      <div className="content">
        <div className="card">
          <h3>Welcome to LinkedIn Ads Action Center</h3>
          <p>Follow the steps below to get started with your ad analytics.</p>
        </div>
        <div className="action-grid">
          {actions.map((a) => (
            <div className="action-card" key={a.step}>
              <div style={{
                display: "inline-flex", alignItems: "center", justifyContent: "center",
                width: 24, height: 24, borderRadius: "50%",
                background: "var(--brand-subtle)", color: "var(--brand)",
                fontSize: 12, fontWeight: 600, marginBottom: "var(--sp-3)"
              }}>
                {a.step}
              </div>
              <h3>{a.title}</h3>
              <p style={{ fontSize: "12.5px", marginBottom: "var(--sp-4)" }}>{a.desc}</p>
              <Link to={a.to} className="btn">Go</Link>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
