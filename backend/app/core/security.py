"""AuthManager: LinkedIn OAuth token management using async httpx."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.errors.exceptions import AuthenticationError, TokenExpiredError
from app.linkedin.constants import (
    API_BASE_URL,
    INTROSPECT_URL,
    LINKEDIN_API_VERSION,
    OAUTH2_BASE_URL,
    SCOPES,
)
from app.utils.logging import get_logger, log_auth_event

logger = get_logger(__name__)

_EXPIRY_BUFFER = 300  # 5 minutes


class AuthManager:
    def __init__(self) -> None:
        self.client_id = settings.LINKEDIN_CLIENT_ID
        self.client_secret = settings.LINKEDIN_CLIENT_SECRET
        self.redirect_uri = settings.LINKEDIN_REDIRECT_URI
        self.tokens_file = Path(settings.tokens_file)
        self.tokens: dict = self._load_tokens()

    # -- Persistence ----------------------------------------------------------

    def _load_tokens(self) -> dict:
        if self.tokens_file.exists():
            with open(self.tokens_file) as f:
                return json.load(f)
        return {}

    def _save_tokens(self) -> None:
        self.tokens["saved_at"] = int(time.time())
        self.tokens_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tokens_file, "w") as f:
            json.dump(self.tokens, f, indent=2)

    # -- OAuth flow -----------------------------------------------------------

    def get_authorization_url(self) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": settings.OAUTH_STATE,
            "scope": " ".join(SCOPES),
        }
        return f"{OAUTH2_BASE_URL}/authorization?{urlencode(params)}"

    async def exchange_code_for_token(self, auth_code: str) -> dict:
        url = f"{OAUTH2_BASE_URL}/accessToken"
        payload = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if resp.status_code >= 400:
            raise AuthenticationError(
                "Failed to exchange authorization code",
                details={"status_code": resp.status_code, "response": resp.text[:500]},
            )

        self.tokens = resp.json()
        now = int(time.time())
        self.tokens["access_token_expires_at"] = now + self.tokens["expires_in"]
        if "refresh_token_expires_in" in self.tokens:
            self.tokens["refresh_token_expires_at"] = (
                now + self.tokens["refresh_token_expires_in"]
            )
        self._save_tokens()
        log_auth_event("Token exchange complete")
        return self.tokens

    async def refresh_access_token(self) -> dict:
        if "refresh_token" not in self.tokens:
            raise AuthenticationError(
                "No refresh token found. Please re-authenticate.",
                details={"tokens_file": str(self.tokens_file)},
            )

        url = f"{OAUTH2_BASE_URL}/accessToken"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"],
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if resp.status_code >= 400:
            raise AuthenticationError(
                "Failed to refresh access token",
                details={"status_code": resp.status_code, "response": resp.text[:500]},
            )

        new = resp.json()
        now = int(time.time())
        self.tokens["access_token"] = new["access_token"]
        self.tokens["expires_in"] = new["expires_in"]
        self.tokens["access_token_expires_at"] = now + new["expires_in"]

        if "refresh_token" in new:
            self.tokens["refresh_token"] = new["refresh_token"]
            self.tokens["refresh_token_expires_in"] = new["refresh_token_expires_in"]
            self.tokens["refresh_token_expires_at"] = (
                now + new["refresh_token_expires_in"]
            )

        self._save_tokens()
        log_auth_event("Token refreshed")
        return self.tokens

    # -- Token access ---------------------------------------------------------

    async def get_access_token(self) -> str:
        if not self.tokens or "access_token" not in self.tokens:
            raise AuthenticationError(
                "Not authenticated. Run the OAuth flow first.",
                details={"tokens_file": str(self.tokens_file)},
            )

        expires_at = self.tokens.get("access_token_expires_at", 0)
        if time.time() >= expires_at - _EXPIRY_BUFFER:
            try:
                await self.refresh_access_token()
            except AuthenticationError:
                raise TokenExpiredError(
                    "Access token expired and refresh failed",
                    token_info={
                        "expires_at": expires_at,
                        "current_time": int(time.time()),
                    },
                )

        return self.tokens["access_token"]

    def is_authenticated(self) -> bool:
        if "access_token" not in self.tokens:
            return False
        expires_at = self.tokens.get("access_token_expires_at", 0)
        return time.time() < expires_at - _EXPIRY_BUFFER

    # -- Diagnostics ----------------------------------------------------------

    async def check_token_health(self) -> bool:
        if not self.is_authenticated():
            await self.refresh_access_token()

        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": LINKEDIN_API_VERSION,
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API_BASE_URL}/me", headers=headers)
                resp.raise_for_status()
            info = resp.json()
            name = f"{info.get('localizedFirstName', '')} {info.get('localizedLastName', '')}".strip()
            log_auth_event("Token valid", f"Authenticated as: {name}")
            return True
        except httpx.HTTPStatusError as exc:
            logger.error("Token validation failed: %d", exc.response.status_code)
            return False

    async def introspect_token(self) -> dict:
        token = await self.get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                INTROSPECT_URL,
                data={
                    "token": token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        resp.raise_for_status()
        return resp.json()

    def token_status(self) -> dict:
        if not self.tokens:
            return {"authenticated": False, "reason": "No tokens on disk."}

        now = time.time()
        at_exp = self.tokens.get("access_token_expires_at", 0)
        rt_exp = self.tokens.get("refresh_token_expires_at", 0)

        return {
            "authenticated": self.is_authenticated(),
            "access_token_expired": now >= at_exp,
            "access_token_days_remaining": max(0, int((at_exp - now) / 86400)),
            "refresh_token_days_remaining": max(0, int((rt_exp - now) / 86400)) if rt_exp else None,
            "saved_at": datetime.fromtimestamp(
                self.tokens.get("saved_at", 0), tz=timezone.utc,
            ).isoformat() if self.tokens.get("saved_at") else None,
        }
