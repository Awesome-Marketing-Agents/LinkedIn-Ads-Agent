"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_tokens():
    """Return a valid mock token dict."""
    import time
    now = int(time.time())
    return {
        "access_token": "mock_access_token_12345",
        "refresh_token": "mock_refresh_token_67890",
        "expires_in": 5184000,
        "refresh_token_expires_in": 31536000,
        "access_token_expires_at": now + 5184000,
        "refresh_token_expires_at": now + 31536000,
        "saved_at": now,
    }


@pytest.fixture
def mock_auth_manager(tmp_path, mock_tokens):
    """Return a mocked AuthManager with valid tokens."""
    from linkedin_action_center.auth.manager import AuthManager
    
    # Create mock tokens file
    tokens_file = tmp_path / "tokens.json"
    import json
    with open(tokens_file, "w") as f:
        json.dump(mock_tokens, f)
    
    # Mock config values
    auth = AuthManager()
    auth.tokens_file = tokens_file
    auth.tokens = mock_tokens
    auth.client_id = "mock_client_id"
    auth.client_secret = "mock_client_secret"
    auth.redirect_uri = "http://localhost:8080/callback"
    
    return auth


@pytest.fixture
def mock_response():
    """Create a mock requests.Response object."""
    mock = MagicMock()
    mock.ok = True
    mock.status_code = 200
    mock.reason = "OK"
    mock.json.return_value = {"elements": []}
    mock.text = ""
    mock.headers = {"content-type": "application/json"}
    return mock


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    from linkedin_action_center.storage.database import init_database
    db_path = tmp_path / "test.db"
    init_database(db_path)
    return db_path
