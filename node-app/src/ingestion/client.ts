/**
 * Low-level HTTP client for the LinkedIn Marketing REST API.
 *
 * Encapsulates authentication headers, pagination, and error handling so that
 * higher-level fetchers never deal with raw HTTP details.
 */

import { AuthManager } from "../auth/manager.js";
import { API_BASE_URL, LINKEDIN_API_VERSION } from "../constants.js";
import { logger } from "../logger.js";
import { LinkedInAPIError, RateLimitError } from "../errors.js";

export class LinkedInClient {
  private auth: AuthManager;

  constructor(auth: AuthManager) {
    this.auth = auth;
  }

  private async headers(): Promise<Record<string, string>> {
    return {
      Authorization: `Bearer ${await this.auth.getAccessToken()}`,
      "LinkedIn-Version": LINKEDIN_API_VERSION,
      "X-Restli-Protocol-Version": "2.0.0",
    };
  }

  /**
   * GET `{API_BASE_URL}{path}?{paramsStr}`.
   *
   * `paramsStr` is a raw query string (already formatted with LinkedIn's
   * special syntax such as `List()` and URN encoding).
   */
  async get(path: string, paramsStr = ""): Promise<Record<string, unknown>> {
    let url = `${API_BASE_URL}${path}`;
    if (paramsStr) url = `${url}?${paramsStr}`;

    const resp = await fetch(url, { headers: await this.headers() });

    if (!resp.ok) {
      // Check for rate limiting
      if (resp.status === 429) {
        const retryAfter = resp.headers.get("Retry-After");
        throw new RateLimitError(
          "API rate limit exceeded",
          retryAfter ? parseInt(retryAfter, 10) : null,
          path,
        );
      }

      const text = await resp.text();
      logger.error(`HTTP ${resp.status} ${resp.statusText} -- ${path}`);
      logger.error(`Response: ${text.slice(0, 500)}`);

      let responseData: Record<string, unknown>;
      try {
        responseData = JSON.parse(text);
      } catch {
        responseData = { text: text.slice(0, 500) };
      }

      throw new LinkedInAPIError(
        `API request failed: ${resp.statusText}`,
        resp.status,
        responseData,
        path,
      );
    }

    return resp.json() as Promise<Record<string, unknown>>;
  }

  /**
   * Paginate through all results for a LinkedIn REST endpoint.
   *
   * Handles both offset-based (start) and token-based (pageToken)
   * pagination transparently.
   */
  async getAllPages(
    path: string,
    paramsStr = "",
    key = "elements",
    pageSize = 100,
  ): Promise<Record<string, unknown>[]> {
    const allItems: Record<string, unknown>[] = [];
    let pageToken: string | null = null;
    let start = 0;

    while (true) {
      const sep = paramsStr ? "&" : "";
      let paged: string;

      if (pageToken) {
        paged = `${paramsStr}${sep}pageToken=${pageToken}&count=${pageSize}`;
      } else {
        paged = `${paramsStr}${sep}start=${start}&count=${pageSize}`;
      }

      const data = await this.get(path, paged);
      const items = (data[key] as Record<string, unknown>[]) ?? [];
      allItems.push(...items);

      // Determine next page
      const metadata = (data.metadata as Record<string, unknown>) ?? {};
      const nextToken = metadata.nextPageToken as string | undefined;

      if (nextToken) {
        pageToken = nextToken;
      } else if (items.length === pageSize) {
        start += pageSize;
      } else {
        break;
      }
    }

    return allItems;
  }

  /**
   * POST to `{API_BASE_URL}{path}`.
   */
  async post(path: string): Promise<Record<string, unknown>> {
    const url = `${API_BASE_URL}${path}`;
    const resp = await fetch(url, {
      method: "POST",
      headers: await this.headers(),
    });

    if (!resp.ok) {
      const text = await resp.text();
      logger.error(`HTTP ${resp.status} ${resp.statusText} -- ${path}`);
      logger.error(`Response: ${text.slice(0, 500)}`);

      let responseData: Record<string, unknown>;
      try {
        responseData = JSON.parse(text);
      } catch {
        responseData = { text: text.slice(0, 500) };
      }

      throw new LinkedInAPIError(
        `API request failed: ${resp.statusText}`,
        resp.status,
        responseData,
        path,
      );
    }

    return resp.json() as Promise<Record<string, unknown>>;
  }
}
