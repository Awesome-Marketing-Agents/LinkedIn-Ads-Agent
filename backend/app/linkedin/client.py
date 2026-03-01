"""Async HTTP client for the LinkedIn Marketing REST API."""

from __future__ import annotations

import time

import httpx

from app.core.security import AuthManager
from app.errors.exceptions import LinkedInAPIError, RateLimitError
from app.linkedin.constants import API_BASE_URL, LINKEDIN_API_VERSION
from app.utils.logging import get_logger, log_api_call

logger = get_logger(__name__)


class LinkedInClient:
    def __init__(self, auth: AuthManager) -> None:
        self._auth = auth

    async def _headers(self) -> dict[str, str]:
        token = await self._auth.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": LINKEDIN_API_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
        }

    async def get(self, path: str, params_str: str = "") -> dict:
        url = f"{API_BASE_URL}{path}"
        if params_str:
            url = f"{url}?{params_str}"

        headers = await self._headers()
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers)
        duration = time.monotonic() - start
        log_api_call("GET", path, resp.status_code, duration)

        if not resp.is_success:
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                raise RateLimitError(
                    endpoint=path,
                    retry_after=int(retry_after) if retry_after else None,
                )
            logger.error("HTTP %d %s -- %s", resp.status_code, resp.reason_phrase, path)
            raise LinkedInAPIError(
                f"API request failed: {resp.reason_phrase}",
                status_code=resp.status_code,
                response_data=resp.json() if "application/json" in resp.headers.get("content-type", "") else {"text": resp.text[:500]},
                endpoint=path,
            )

        return resp.json()

    async def get_all_pages(
        self,
        path: str,
        params_str: str = "",
        key: str = "elements",
        page_size: int = 100,
    ) -> list[dict]:
        all_items: list[dict] = []
        page_token: str | None = None
        start = 0

        while True:
            sep = "&" if params_str else ""
            if page_token:
                paged = f"{params_str}{sep}pageToken={page_token}&count={page_size}"
            else:
                paged = f"{params_str}{sep}start={start}&count={page_size}"

            data = await self.get(path, paged)
            items = data.get(key, [])
            all_items.extend(items)

            metadata = data.get("metadata", {})
            next_token = metadata.get("nextPageToken")

            if next_token:
                page_token = next_token
            elif len(items) == page_size:
                start += page_size
            else:
                break

        return all_items
