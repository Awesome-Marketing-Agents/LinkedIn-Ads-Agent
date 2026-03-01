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
  Menu,
} from "lucide-react";
import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
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
  onClick,
}: {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  onClick?: () => void;
}) {
  const matchRoute = useMatchRoute();
  const isActive =
    to === "/" ? matchRoute({ to: "/" }) : matchRoute({ to, fuzzy: true });

  return (
    <Link
      to={to}
      onClick={onClick}
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

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <>
      <nav className="flex-1 px-2 space-y-5">
        {navSections.map((section) => (
          <div key={section.title}>
            <div className="mb-1.5 px-2.5 text-[10px] font-semibold uppercase tracking-[0.1em] text-ink-faint/60">
              {section.title}
            </div>
            <div className="space-y-px">
              {section.links.map((link) => (
                <NavItem key={link.to} {...link} onClick={onNavigate} />
              ))}
            </div>
          </div>
        ))}
      </nav>
    </>
  );
}

export function Layout() {
  const [dark, setDark] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("theme");
      if (saved) return saved === "dark";
    }
    return true;
  });
  const [sheetOpen, setSheetOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  const themeButton = (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => setDark(!dark)}
      className="w-full justify-start gap-2.5 px-2.5 text-[11px] text-ink-faint hover:text-foreground"
    >
      {dark ? (
        <Sun className="h-3.5 w-3.5" />
      ) : (
        <Moon className="h-3.5 w-3.5" />
      )}
      {dark ? "Light mode" : "Dark mode"}
    </Button>
  );

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-50 hidden md:flex w-52 flex-col border-r border-border">
        <div className="px-4 pt-5 pb-4">
          <div className="text-[13px] font-semibold tracking-tight text-foreground">
            LinkedIn Ads
          </div>
          <div className="text-[10px] font-medium uppercase tracking-[0.08em] text-ink-faint mt-0.5">
            Action Center
          </div>
        </div>

        <SidebarContent />

        <div className="border-t border-border px-2 py-2 space-y-0.5">
          <FreshnessIndicator />
          {themeButton}
        </div>
      </aside>

      {/* Mobile header + Sheet */}
      <div className="fixed top-0 left-0 right-0 z-50 flex md:hidden h-12 items-center border-b border-border bg-background px-3 gap-3">
        <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon-sm">
              <Menu className="h-4 w-4" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-52 p-0">
            <div className="px-4 pt-5 pb-4">
              <SheetTitle className="text-[13px] font-semibold tracking-tight text-foreground">
                LinkedIn Ads
              </SheetTitle>
              <div className="text-[10px] font-medium uppercase tracking-[0.08em] text-ink-faint mt-0.5">
                Action Center
              </div>
            </div>
            <SidebarContent onNavigate={() => setSheetOpen(false)} />
            <div className="border-t border-border px-2 py-2 space-y-0.5">
              <FreshnessIndicator />
              {themeButton}
            </div>
          </SheetContent>
        </Sheet>
        <div className="text-[13px] font-semibold tracking-tight text-foreground">
          LinkedIn Ads
        </div>
      </div>

      <div className="md:ml-52 flex-1 min-h-screen pt-12 md:pt-0">
        <Outlet />
      </div>
    </div>
  );
}
