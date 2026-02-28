/**
 * Token management: load, save, refresh, validate LinkedIn OAuth tokens.
 */

import fs from "node:fs";
import { env, TOKENS_FILE } from "../config.js";
import {
  OAUTH2_BASE_URL,
  INTROSPECT_URL,
  API_BASE_URL,
  LINKEDIN_API_VERSION,
  SCOPES,
} from "../constants.js";
import { AuthenticationError, TokenExpiredError } from "../errors.js";
import { logger, logAuthEvent } from "../logger.js";

// Buffer in seconds before considering a token expired (5 minutes)
const EXPIRY_BUFFER = 300;

interface TokenData {
  access_token?: string;
  refresh_token?: string;
  expires_in?: number;
  refresh_token_expires_in?: number;
  access_token_expires_at?: number;
  refresh_token_expires_at?: number;
  saved_at?: number;
  [key: string]: unknown;
}

export class AuthManager {
  private clientId: string;
  private clientSecret: string;
  private redirectUri: string;
  private tokensFile: string;
  tokens: TokenData;

  constructor() {
    this.clientId = env.LINKEDIN_CLIENT_ID;
    this.clientSecret = env.LINKEDIN_CLIENT_SECRET;
    this.redirectUri = env.LINKEDIN_REDIRECT_URI;
    this.tokensFile = TOKENS_FILE;
    this.tokens = this.loadTokens();
  }

  // -- Persistence ----------------------------------------------------------

  private loadTokens(): TokenData {
    try {
      if (fs.existsSync(this.tokensFile)) {
        const data = fs.readFileSync(this.tokensFile, "utf-8");
        return JSON.parse(data);
      }
    } catch {
      // Ignore parse errors, start fresh
    }
    return {};
  }

  private saveTokens(): void {
    this.tokens.saved_at = Math.floor(Date.now() / 1000);
    fs.writeFileSync(this.tokensFile, JSON.stringify(this.tokens, null, 2));
  }

  // -- OAuth flow -----------------------------------------------------------

  getAuthorizationUrl(): string {
    const params = new URLSearchParams({
      response_type: "code",
      client_id: this.clientId,
      redirect_uri: this.redirectUri,
      state: env.OAUTH_STATE,
      scope: SCOPES.join(" "),
    });
    return `${OAUTH2_BASE_URL}/authorization?${params.toString()}`;
  }

  async exchangeCodeForToken(authCode: string): Promise<TokenData> {
    const url = `${OAUTH2_BASE_URL}/accessToken`;
    const body = new URLSearchParams({
      grant_type: "authorization_code",
      code: authCode,
      client_id: this.clientId,
      client_secret: this.clientSecret,
      redirect_uri: this.redirectUri,
    });

    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });

    if (!resp.ok) {
      const text = await resp.text();
      throw new AuthenticationError("Failed to exchange authorization code", {
        status_code: resp.status,
        response: text.slice(0, 500),
      });
    }

    this.tokens = (await resp.json()) as TokenData;
    const now = Math.floor(Date.now() / 1000);
    this.tokens.access_token_expires_at = now + (this.tokens.expires_in ?? 0);
    if (this.tokens.refresh_token_expires_in) {
      this.tokens.refresh_token_expires_at =
        now + this.tokens.refresh_token_expires_in;
    }
    this.saveTokens();
    return this.tokens;
  }

  async refreshAccessToken(): Promise<TokenData> {
    if (!this.tokens.refresh_token) {
      throw new AuthenticationError(
        "No refresh token found. Please re-authenticate.",
        { tokens_file: this.tokensFile },
      );
    }

    const url = `${OAUTH2_BASE_URL}/accessToken`;
    const body = new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: this.tokens.refresh_token,
      client_id: this.clientId,
      client_secret: this.clientSecret,
    });

    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });

    if (!resp.ok) {
      const text = await resp.text();
      throw new AuthenticationError("Failed to refresh access token", {
        status_code: resp.status,
        response: text.slice(0, 500),
      });
    }

    const newTokens = (await resp.json()) as TokenData;
    const now = Math.floor(Date.now() / 1000);

    this.tokens.access_token = newTokens.access_token;
    this.tokens.expires_in = newTokens.expires_in;
    this.tokens.access_token_expires_at = now + (newTokens.expires_in ?? 0);

    // LinkedIn may or may not return a new refresh token
    if (newTokens.refresh_token) {
      this.tokens.refresh_token = newTokens.refresh_token;
      this.tokens.refresh_token_expires_in =
        newTokens.refresh_token_expires_in;
      this.tokens.refresh_token_expires_at =
        now + (newTokens.refresh_token_expires_in ?? 0);
    }

    this.saveTokens();
    return this.tokens;
  }

  // -- Token access ---------------------------------------------------------

  async getAccessToken(): Promise<string> {
    if (!this.tokens || !this.tokens.access_token) {
      throw new AuthenticationError(
        "Not authenticated. Run the OAuth flow first.",
        { tokens_file: this.tokensFile },
      );
    }

    const expiresAt = this.tokens.access_token_expires_at ?? 0;
    const now = Math.floor(Date.now() / 1000);

    if (now >= expiresAt - EXPIRY_BUFFER) {
      try {
        await this.refreshAccessToken();
      } catch {
        throw new TokenExpiredError(
          "Access token expired and refresh failed",
          { expires_at: expiresAt, current_time: now },
        );
      }
    }

    return this.tokens.access_token!;
  }

  isAuthenticated(): boolean {
    if (!this.tokens.access_token) return false;
    const expiresAt = this.tokens.access_token_expires_at ?? 0;
    return Math.floor(Date.now() / 1000) < expiresAt - EXPIRY_BUFFER;
  }

  // -- Diagnostics ----------------------------------------------------------

  async checkTokenHealth(): Promise<boolean> {
    if (!this.isAuthenticated()) {
      await this.refreshAccessToken();
    }

    const token = await this.getAccessToken();
    const headers = {
      Authorization: `Bearer ${token}`,
      "X-Restli-Protocol-Version": "2.0.0",
      "LinkedIn-Version": LINKEDIN_API_VERSION,
    };

    try {
      const resp = await fetch(`${API_BASE_URL}/me`, { headers });
      if (!resp.ok) {
        logger.error(`Token validation failed: ${resp.status}`);
        return false;
      }
      const info = (await resp.json()) as Record<string, string>;
      const name =
        `${info.localizedFirstName ?? ""} ${info.localizedLastName ?? ""}`.trim();
      logAuthEvent("Token valid", `Authenticated as: ${name}`);
      return true;
    } catch (err) {
      logger.error(`Token validation failed: ${err}`);
      return false;
    }
  }

  async introspectToken(): Promise<Record<string, unknown>> {
    const token = await this.getAccessToken();
    const body = new URLSearchParams({
      token,
      client_id: this.clientId,
      client_secret: this.clientSecret,
    });

    const resp = await fetch(INTROSPECT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });

    if (!resp.ok) throw new Error(`Introspect failed: ${resp.status}`);
    return resp.json() as Promise<Record<string, unknown>>;
  }

  tokenStatus(): Record<string, unknown> {
    if (!this.tokens || Object.keys(this.tokens).length === 0) {
      return { authenticated: false, reason: "No tokens on disk." };
    }

    const now = Math.floor(Date.now() / 1000);
    const atExp = this.tokens.access_token_expires_at ?? 0;
    const rtExp = this.tokens.refresh_token_expires_at ?? 0;

    return {
      authenticated: this.isAuthenticated(),
      access_token_expired: now >= atExp,
      access_token_days_remaining: Math.max(
        0,
        Math.floor((atExp - now) / 86400),
      ),
      refresh_token_days_remaining: rtExp
        ? Math.max(0, Math.floor((rtExp - now) / 86400))
        : null,
      saved_at: this.tokens.saved_at
        ? new Date(this.tokens.saved_at * 1000).toISOString()
        : null,
    };
  }
}
