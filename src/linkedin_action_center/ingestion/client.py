"""Low-level HTTP client for the LinkedIn Marketing REST API.

Encapsulates authentication headers, pagination, and error handling so that
higher-level fetchers never deal with raw HTTP details.
"""

from __future__ import annotations

import requests

from linkedin_action_center.auth.manager import AuthManager
from linkedin_action_center.core.constants import API_BASE_URL, LINKEDIN_API_VERSION
from linkedin_action_center.utils.logger import logger
from linkedin_action_center.utils.errors import (
    LinkedInAPIError,
    RateLimitError,
)


class LinkedInClient:
    """Thin wrapper around ``requests`` pre-configured for the LinkedIn REST API."""

    def __init__(self, auth: AuthManager):
        self._auth = auth

    # Internal helpers

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._auth.get_access_token()}",
            "LinkedIn-Version": LINKEDIN_API_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
        }

    # Core HTTP methods

    def get(self, path: str, params_str: str = "") -> dict:
        """
        GET ``{API_BASE_URL}{path}?{params_str}``.

        ``params_str`` is a *raw* query string (already formatted with
        LinkedIn's special syntax such as ``List()`` and URN encoding).
        Raises on non-2xx responses after printing diagnostic info.
        """
        url = f"{API_BASE_URL}{path}"
        if params_str:
            url = f"{url}?{params_str}"

        resp = requests.get(url, headers=self._headers())
        if not resp.ok:
            # Check for rate limiting
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                raise RateLimitError(
                    endpoint=path,
                    retry_after=int(retry_after) if retry_after else None
                )
            
            # Log and raise general API error
            logger.error(f"HTTP {resp.status_code} {resp.reason} -- {path}")
            logger.error(f"Response: {resp.text[:500]}")
            
            raise LinkedInAPIError(
                f"API request failed: {resp.reason}",
                status_code=resp.status_code,
                response_data=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"text": resp.text[:500]},
                endpoint=path
            )
        
        return resp.json()

    def get_all_pages(
        self,
        path: str,
        params_str: str = "",
        key: str = "elements",
        page_size: int = 100,
    ) -> list[dict]:
        """
        Paginate through *all* results for a LinkedIn REST endpoint.

        Handles both offset-based (``start``) and token-based
        (``pageToken``) pagination transparently.
        """
        all_items: list[dict] = []
        page_token: str | None = None
        start = 0

        while True:
            sep = "&" if params_str else ""
            if page_token:
                paged = f"{params_str}{sep}pageToken={page_token}&count={page_size}"
            else:
                paged = f"{params_str}{sep}start={start}&count={page_size}"

            data = self.get(path, paged)
            items = data.get(key, [])
            all_items.extend(items)

            # Determine next page
            metadata = data.get("metadata", {})
            next_token = metadata.get("nextPageToken")

            if next_token:
                page_token = next_token
            elif len(items) == page_size:
                start += page_size
            else:
                break

        return all_items
