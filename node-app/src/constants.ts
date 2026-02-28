export const LINKEDIN_API_VERSION = "202602" as const;

// API Endpoints
export const OAUTH2_BASE_URL = "https://www.linkedin.com/oauth/v2" as const;
export const INTROSPECT_URL =
  "https://www.linkedin.com/oauth/v2/introspectToken" as const;
export const API_BASE_URL = "https://api.linkedin.com/rest" as const;

// OAuth Scopes
export const SCOPES = ["r_ads", "r_ads_reporting", "r_basicprofile"] as const;
