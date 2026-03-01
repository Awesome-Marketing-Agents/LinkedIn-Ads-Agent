"""Tests for AuthManager (async httpx)."""

import json
import time
from unittest.mock import AsyncMock, patch

import pytest

from app.core.security import AuthManager
from app.errors.exceptions import AuthenticationError


@pytest.fixture
def auth_manager(tmp_path, mock_tokens):
    tokens_file = tmp_path / "tokens.json"
    tokens_file.write_text(json.dumps(mock_tokens))

    with patch("app.core.security.settings") as mock_settings:
        mock_settings.LINKEDIN_CLIENT_ID = "test_id"
        mock_settings.LINKEDIN_CLIENT_SECRET = "test_secret"
        mock_settings.LINKEDIN_REDIRECT_URI = "http://localhost:8000/callback"
        mock_settings.OAUTH_STATE = "teststate"
        mock_settings.tokens_file = tokens_file

        mgr = AuthManager()
        mgr.tokens = mock_tokens
        mgr.tokens_file = tokens_file
        yield mgr


def test_is_authenticated(auth_manager):
    assert auth_manager.is_authenticated() is True


def test_not_authenticated_no_tokens(tmp_path):
    with patch("app.core.security.settings") as mock_settings:
        mock_settings.LINKEDIN_CLIENT_ID = "test"
        mock_settings.LINKEDIN_CLIENT_SECRET = "test"
        mock_settings.LINKEDIN_REDIRECT_URI = "http://localhost:8000/callback"
        mock_settings.OAUTH_STATE = "teststate"
        mock_settings.tokens_file = tmp_path / "nonexistent.json"

        mgr = AuthManager()
        assert mgr.is_authenticated() is False


def test_token_status(auth_manager):
    status = auth_manager.token_status()
    assert status["authenticated"] is True
    assert status["access_token_days_remaining"] > 0


def test_get_authorization_url(auth_manager):
    url = auth_manager.get_authorization_url()
    assert "linkedin.com/oauth/v2/authorization" in url
    assert "client_id=" in url


@pytest.mark.asyncio
async def test_exchange_code_raises_on_failure(auth_manager):
    mock_resp = AsyncMock()
    mock_resp.status_code = 400
    mock_resp.text = "Bad Request"

    with patch("app.core.security.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        with pytest.raises(AuthenticationError):
            await auth_manager.exchange_code_for_token("bad_code")
