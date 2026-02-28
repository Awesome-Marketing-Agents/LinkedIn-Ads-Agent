import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  {
    section: "Navigation",
    links: [
      { to: "/", label: "Dashboard", icon: "M2 6l6-4.5L14 6v7.5a1 1 0 01-1 1H3a1 1 0 01-1-1V6z M6 14.5V8h4v6.5" },
      { to: "/auth", label: "Auth", icon: "M2 7h12v7H2z M4.5 7V5a3.5 3.5 0 117 0v2" },
      { to: "/sync", label: "Sync Data", icon: "M1 8a7 7 0 0113.16-3.36 M15 8a7 7 0 01-13.16 3.36" },
    ],
  },
  {
    section: "Analysis",
    links: [
      { to: "/visual", label: "Visual Dashboard", icon: "M2 2v12h12 M5 11l3-4 2 2 3-4" },
      { to: "/report", label: "Report Tables", icon: "M2 2v12h12 M5 10V8 M8 10V6 M11 10V4" },
      { to: "/status", label: "Status", icon: "M8 2a6 6 0 100 12A6 6 0 008 2z M8 5v3l2 1.5" },
    ],
  },
];

export function Layout() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>LinkedIn Ads</h1>
          <span>Action Center</span>
        </div>
        {navItems.map((section) => (
          <div key={section.section}>
            <div className="sidebar-section">{section.section}</div>
            <nav>
              {section.links.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) => (isActive ? "active" : "")}
                  end={link.to === "/"}
                >
                  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                    {link.icon.split(" M").map((d, i) => (
                      <path key={i} d={i === 0 ? d : `M${d}`} />
                    ))}
                  </svg>
                  {link.label}
                </NavLink>
              ))}
            </nav>
          </div>
        ))}
      </aside>
      <div className="main">
        <Outlet />
      </div>
    </div>
  );
}
