import { useQuery } from "@tanstack/react-query";
import type { TokenStatus } from "@/types";
import { createLogger } from "@/lib/logger";

const logger = createLogger("useAuth");

async function fetchAuthStatus(): Promise<TokenStatus> {
  const res = await fetch("/api/v1/auth/status");
  if (!res.ok) throw new Error(`Auth status failed: ${res.status}`);
  return res.json();
}

async function fetchAuthUrl(): Promise<string> {
  const res = await fetch("/api/v1/auth/url");
  if (!res.ok) throw new Error(`Auth URL failed: ${res.status}`);
  const data = await res.json();
  return data.url;
}

export function useAuthStatus() {
  return useQuery({
    queryKey: ["auth", "status"],
    queryFn: fetchAuthStatus,
  });
}

export function useStartAuth() {
  return async () => {
    logger.info("Starting OAuth flow");
    const url = await fetchAuthUrl();
    window.location.href = url;
  };
}
