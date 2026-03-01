import { useQuery } from "@tanstack/react-query";
import type { VisualData, StatusData } from "@/types";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export function useVisualData() {
  return useQuery({
    queryKey: ["report", "visual"],
    queryFn: () => fetchJson<VisualData>("/api/v1/report/visual"),
  });
}

export function useCampaignMetrics(page: number, pageSize = 50) {
  return useQuery({
    queryKey: ["report", "campaign-metrics", page, pageSize],
    queryFn: () =>
      fetchJson<Record<string, unknown>>(
        `/api/v1/report/campaign-metrics?page=${page}&page_size=${pageSize}`,
      ),
  });
}

export function useCreativeMetrics(page: number, pageSize = 50) {
  return useQuery({
    queryKey: ["report", "creative-metrics", page, pageSize],
    queryFn: () =>
      fetchJson<Record<string, unknown>>(
        `/api/v1/report/creative-metrics?page=${page}&page_size=${pageSize}`,
      ),
  });
}

export function useDemographics(pivotType?: string) {
  return useQuery({
    queryKey: ["report", "demographics", pivotType],
    queryFn: () =>
      fetchJson<Record<string, unknown>>(
        `/api/v1/report/demographics${pivotType ? `?pivot_type=${pivotType}` : ""}`,
      ),
  });
}

export function useStatus() {
  return useQuery({
    queryKey: ["status"],
    queryFn: () => fetchJson<StatusData>("/api/v1/status"),
  });
}
