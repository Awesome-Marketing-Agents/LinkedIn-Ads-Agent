import { Outlet, Link, useMatchRoute } from "@tanstack/react-router";
import {
  LayoutDashboard,
  KeyRound,
  RefreshCw,
  BarChart3,
  Table2,
  Activity,
  Moon,
  Sun,
  Radio,
} from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import type { TokenStatus } from "@/types";

const navSections = [
  {
    title: "Operate",
    links: [
      { to: "/", label: "Overview", icon: LayoutDashboard },
      { to: "/auth", label: "Connection", icon: KeyRound },
      { to: "/sync", label: "Sync", icon: RefreshCw },
    ],
  },
  {
    title: "Analyze",
    links: [
      { to: "/visual", label: "Performance", icon: BarChart3 },
      { to: "/report", label: "Tables", icon: Table2 },
      { to: "/status", label: "System", icon: Activity },
    ],
  },
] as const;

function NavItem({
  to,
  label,
  icon: Icon,
}: {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  const matchRoute = useMatchRoute();
  const isActive =
    to === "/" ? matchRoute({ to: "/" }) : matchRoute({ to, fuzzy: true });

  return (
    <Link
      to={to}
      className={cn(
        "flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] font-medium transition-colors",
        isActive
          ? "bg-accent-muted text-primary"
          : "text-ink-faint hover:text-foreground hover:bg-accent-muted/50",
      )}
    >
      <Icon className="h-[15px] w-[15px] shrink-0" />
      {label}
    </Link>
  );
}

function FreshnessIndicator() {
  const { data } = useQuery<TokenStatus>({
    queryKey: ["auth", "status"],
    queryFn: async () => {
      const res = await fetch("/api/v1/auth/status");
      return res.json();
    },
    staleTime: 60_000,
    retry: false,
  });

  const connected = data?.authenticated ?? false;

  return (
    <div className="flex items-center gap-2 px-2.5 py-2">
      <Radio className={cn("h-3 w-3", connected ? "text-signal-positive" : "text-signal-error")} />
      <span className="text-[11px] text-ink-faint">
        {connected ? "Connected" : "Disconnected"}
      </span>
    </div>
  );
}

export function Layout() {
  const [dark, setDark] = useState(true);

  const toggleTheme = () => {
    setDark(!dark);
    document.documentElement.classList.toggle("dark");
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar — shares canvas background, border-only separation */}
      <aside className="fixed inset-y-0 left-0 z-50 flex w-52 flex-col border-r border-border">
        <div className="px-4 pt-5 pb-4">
          <div className="text-[13px] font-semibold tracking-tight text-foreground">
            LinkedIn Ads
          </div>
          <div className="text-[10px] font-medium uppercase tracking-[0.08em] text-ink-faint mt-0.5">
            Action Center
          </div>
        </div>

        <nav className="flex-1 px-2 space-y-5">
          {navSections.map((section) => (
            <div key={section.title}>
              <div className="mb-1.5 px-2.5 text-[10px] font-semibold uppercase tracking-[0.1em] text-ink-faint/60">
                {section.title}
              </div>
              <div className="space-y-px">
                {section.links.map((link) => (
                  <NavItem key={link.to} {...link} />
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-border px-2 py-2 space-y-0.5">
          <FreshnessIndicator />
          <button
            onClick={toggleTheme}
            className="flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[11px] text-ink-faint hover:text-foreground hover:bg-accent-muted/50 transition-colors"
          >
            {dark ? (
              <Sun className="h-3.5 w-3.5" />
            ) : (
              <Moon className="h-3.5 w-3.5" />
            )}
            {dark ? "Light mode" : "Dark mode"}
          </button>
        </div>
      </aside>

      <div className="ml-52 flex-1 min-h-screen">
        <Outlet />
      </div>
    </div>
  );
}
