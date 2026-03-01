"""Tests for LinkedIn API client (async httpx)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.errors.exceptions import LinkedInAPIError, RateLimitError
from app.linkedin.client import LinkedInClient


@pytest.fixture
def mock_auth():
    auth = AsyncMock()
    auth.get_access_token = AsyncMock(return_value="mock_token")
    return auth


@pytest.fixture
def linkedin_client(mock_auth):
    return LinkedInClient(mock_auth)


@pytest.mark.asyncio
async def test_get_success(linkedin_client):
    mock_resp = MagicMock()
    mock_resp.is_success = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"elements": [{"id": 1}]}
    mock_resp.headers = {"content-type": "application/json"}

    with patch("app.linkedin.client.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = mock_client

        result = await linkedin_client.get("/test")
        assert result == {"elements": [{"id": 1}]}


@pytest.mark.asyncio
async def test_get_rate_limit(linkedin_client):
    mock_resp = MagicMock()
    mock_resp.is_success = False
    mock_resp.status_code = 429
    mock_resp.reason_phrase = "Too Many Requests"
    mock_resp.headers = {"Retry-After": "60"}

    with patch("app.linkedin.client.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = mock_client

        with pytest.raises(RateLimitError):
            await linkedin_client.get("/test")


@pytest.mark.asyncio
async def test_get_api_error(linkedin_client):
    mock_resp = MagicMock()
    mock_resp.is_success = False
    mock_resp.status_code = 500
    mock_resp.reason_phrase = "Internal Server Error"
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"message": "error"}
    mock_resp.text = "error"

    with patch("app.linkedin.client.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = mock_client

        with pytest.raises(LinkedInAPIError):
            await linkedin_client.get("/test")
