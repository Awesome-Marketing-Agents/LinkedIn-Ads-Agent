export interface TokenStatus {
  authenticated: boolean;
  access_token_expired?: boolean;
  access_token_days_remaining?: number;
  refresh_token_days_remaining?: number | null;
  saved_at?: string | null;
  reason?: string;
}

export interface SyncJobResponse {
  job_id: string;
  status: string;
}

export interface SyncProgress {
  step: string;
  detail: string;
}

export interface PaginatedResponse<T> {
  rows: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CampaignMetricRow {
  campaign_id: number;
  campaign_name: string;
  date: string;
  impressions: number;
  clicks: number;
  spend: number;
  ctr: number;
  cpc: number;
  landing_page_clicks: number;
  conversions: number;
}

export interface CreativeMetricRow {
  creative_id: string;
  date: string;
  impressions: number;
  clicks: number;
  spend: number;
  ctr: number;
  cpc: number;
}

export interface DemographicRow {
  pivot_type: string;
  segment: string;
  impressions: number;
  clicks: number;
  ctr: number;
  share_pct: number;
}

export interface VisualData {
  time_series: Array<{
    date: string;
    impressions: number;
    clicks: number;
    spend: number;
    conversions: number;
  }>;
  campaign_comparison: Array<{
    name: string;
    impressions: number;
    clicks: number;
    spend: number;
    conversions: number;
  }>;
  kpis: {
    impressions: number;
    clicks: number;
    spend: number;
    conversions: number;
    ctr: number;
    cpc: number;
    cpm: number;
  };
}

export interface StatusData {
  token: TokenStatus;
  database: Record<string, number>;
  active_campaign_audit: Array<{ name: string; issues: string[] }>;
}
