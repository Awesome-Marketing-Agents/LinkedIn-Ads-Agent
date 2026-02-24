"""Token management: load, save, refresh, validate LinkedIn OAuth tokens."""

import json
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from linkedin_action_center.utils.logger import logger, log_auth_event
from linkedin_action_center.utils.errors import (
    AuthenticationError,
    TokenExpiredError,
)
from linkedin_action_center.core.config import (
    LINKEDIN_CLIENT_ID,
    LINKEDIN_CLIENT_SECRET,
    LINKEDIN_REDIRECT_URI,
    TOKENS_FILE,
    OAUTH_STATE,
)
from linkedin_action_center.core.constants import (
    OAUTH2_BASE_URL,
    INTROSPECT_URL,
    API_BASE_URL,
    LINKEDIN_API_VERSION,
    SCOPES,
)

# Buffer in seconds before considering a token expired (5 minutes)
_EXPIRY_BUFFER = 300


class AuthManager:
    """Handles LinkedIn API authentication, including token management and refresh."""

    def __init__(self):
        self.client_id = LINKEDIN_CLIENT_ID
        self.client_secret = LINKEDIN_CLIENT_SECRET
        self.redirect_uri = LINKEDIN_REDIRECT_URI
        self.tokens_file = Path(TOKENS_FILE)
        self.tokens = self._load_tokens()

    # -- Persistence ----------------------------------------------------------

    def _load_tokens(self) -> dict:
        """Load tokens from the JSON file if it exists."""
        if self.tokens_file.exists():
            with open(self.tokens_file, "r") as f:
                return json.load(f)
        return {}

    def _save_tokens(self):
        """Persist current token dict to disk."""
        self.tokens["saved_at"] = int(time.time())
        with open(self.tokens_file, "w") as f:
            json.dump(self.tokens, f, indent=2)

    # -- OAuth flow -----------------------------------------------------------

    def get_authorization_url(self) -> str:
        """Build the LinkedIn authorization URL the user must visit."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": OAUTH_STATE,
            "scope": " ".join(SCOPES),
        }
        return f"{OAUTH2_BASE_URL}/authorization?{urlencode(params)}"

    def exchange_code_for_token(self, auth_code: str) -> dict:
        """Exchange an authorization code for access + refresh tokens."""
        url = f"{OAUTH2_BASE_URL}/accessToken"
        payload = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }
        resp = requests.post(
            url, data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if not resp.ok:
            raise AuthenticationError(
                "Failed to exchange authorization code",
                details={
                    "status_code": resp.status_code,
                    "response": resp.text[:500],
                }
            )

        self.tokens = resp.json()
        now = int(time.time())
        self.tokens["access_token_expires_at"] = now + self.tokens["expires_in"]
        if "refresh_token_expires_in" in self.tokens:
            self.tokens["refresh_token_expires_at"] = (
                now + self.tokens["refresh_token_expires_in"]
            )
        self._save_tokens()
        return self.tokens

    def refresh_access_token(self) -> dict:
        """Use the refresh token to obtain a new access token."""
        if "refresh_token" not in self.tokens:
            raise AuthenticationError(
                "No refresh token found. Please re-authenticate.",
                details={"tokens_file": str(self.tokens_file)}
            )

        url = f"{OAUTH2_BASE_URL}/accessToken"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"],
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        resp = requests.post(
            url, data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if not resp.ok:
            raise AuthenticationError(
                "Failed to refresh access token",
                details={
                    "status_code": resp.status_code,
                    "response": resp.text[:500],
                }
            )

        new = resp.json()
        now = int(time.time())

        self.tokens["access_token"] = new["access_token"]
        self.tokens["expires_in"] = new["expires_in"]
        self.tokens["access_token_expires_at"] = now + new["expires_in"]

        # LinkedIn may or may not return a new refresh token.
        if "refresh_token" in new:
            self.tokens["refresh_token"] = new["refresh_token"]
            self.tokens["refresh_token_expires_in"] = new["refresh_token_expires_in"]
            self.tokens["refresh_token_expires_at"] = (
                now + new["refresh_token_expires_in"]
            )

        self._save_tokens()
        return self.tokens

    # -- Token access ---------------------------------------------------------

    def get_access_token(self) -> str:
        """
        Return a valid access token, refreshing automatically if expired.
        This is the primary method other modules should call.
        """
        if not self.tokens or "access_token" not in self.tokens:
            raise AuthenticationError(
                "Not authenticated. Run the OAuth flow first.",
                details={"tokens_file": str(self.tokens_file)}
            )

        expires_at = self.tokens.get("access_token_expires_at", 0)
        if time.time() >= expires_at - _EXPIRY_BUFFER:
            try:
                self.refresh_access_token()
            except AuthenticationError:
                raise TokenExpiredError(
                    "Access token expired and refresh failed",
                    token_info={
                        "expires_at": expires_at,
                        "current_time": int(time.time()),
                    }
                )

        return self.tokens["access_token"]

    def is_authenticated(self) -> bool:
        """Return True if a non-expired access token exists."""
        if "access_token" not in self.tokens:
            return False
        expires_at = self.tokens.get("access_token_expires_at", 0)
        return time.time() < expires_at - _EXPIRY_BUFFER

    # -- Diagnostics ----------------------------------------------------------

    def check_token_health(self) -> bool:
        """Make a lightweight API call to verify the token works."""
        if not self.is_authenticated():
            self.refresh_access_token()

        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": LINKEDIN_API_VERSION,
        }
        try:
            resp = requests.get(f"{API_BASE_URL}/me", headers=headers)
            resp.raise_for_status()
            info = resp.json()
            name = f"{info.get('localizedFirstName', '')} {info.get('localizedLastName', '')}".strip()
            log_auth_event("Token valid", f"Authenticated as: {name}")
            return True
        except requests.exceptions.HTTPError as exc:
            logger.error(f"Token validation failed: {exc.response.status_code}")
            return False

    def introspect_token(self) -> dict:
        """Call LinkedIn's introspect endpoint to get token metadata."""
        token = self.get_access_token()
        resp = requests.post(
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
        """Return a summary dict describing current token health."""
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
                self.tokens.get("saved_at", 0), tz=timezone.utc
            ).isoformat() if self.tokens.get("saved_at") else None,
        }

