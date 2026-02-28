const BASE = "";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  getAuthStatus: () => fetchJson<Record<string, unknown>>("/api/auth/status"),
  getAuthUrl: () => fetchJson<{ url: string }>("/api/auth/url"),
  getStatus: () => fetchJson<Record<string, unknown>>("/api/status"),
  startSync: () =>
    fetch("/api/sync", { method: "POST" }).then((r) => r.json() as Promise<{ jobId: string }>),
  getVisualData: () => fetchJson<Record<string, unknown>>("/api/report/visual"),
  getCampaignMetrics: (page = 1, pageSize = 50) =>
    fetchJson<Record<string, unknown>>(`/api/report/campaign-metrics?page=${page}&pageSize=${pageSize}`),
  getCreativeMetrics: (page = 1, pageSize = 50) =>
    fetchJson<Record<string, unknown>>(`/api/report/creative-metrics?page=${page}&pageSize=${pageSize}`),
  getDemographics: (pivotType?: string) =>
    fetchJson<Record<string, unknown>>(
      `/api/report/demographics${pivotType ? `?pivot_type=${pivotType}` : ""}`,
    ),
  getCampaigns: () => fetchJson<Record<string, unknown>>("/api/report/campaigns"),
  getAccounts: () => fetchJson<Record<string, unknown>>("/api/report/accounts"),
};
