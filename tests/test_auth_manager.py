"""Unit tests for AuthManager."""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from linkedin_action_center.auth.manager import AuthManager
from linkedin_action_center.utils.errors import AuthenticationError, TokenExpiredError


class TestAuthManagerInit:
    """Test AuthManager initialization."""
    
    def test_init_without_tokens_file(self, tmp_path):
        """Test initializing without existing tokens."""
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tmp_path / "tokens.json")):
            auth = AuthManager()
            assert auth.tokens == {}
            assert isinstance(auth.tokens_file, Path)
    
    def test_init_with_existing_tokens(self, tmp_path, mock_tokens):
        """Test initializing with existing tokens file."""
        tokens_file = tmp_path / "tokens.json"
        with open(tokens_file, "w") as f:
            json.dump(mock_tokens, f)
        
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            assert auth.tokens["access_token"] == mock_tokens["access_token"]
            assert "refresh_token" in auth.tokens


class TestTokenPersistence:
    """Test token loading and saving."""
    
    def test_save_tokens(self, tmp_path, mock_tokens):
        """Test saving tokens to disk."""
        tokens_file = tmp_path / "tokens.json"
        
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            auth.tokens = mock_tokens.copy()
            auth._save_tokens()
            
            # Verify file was created
            assert tokens_file.exists()
            
            # Verify content
            with open(tokens_file, "r") as f:
                saved = json.load(f)
            assert saved["access_token"] == mock_tokens["access_token"]
            assert "saved_at" in saved
    
    def test_load_tokens(self, tmp_path, mock_tokens):
        """Test loading tokens from disk."""
        tokens_file = tmp_path / "tokens.json"
        with open(tokens_file, "w") as f:
            json.dump(mock_tokens, f)
        
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            loaded = auth._load_tokens()
            assert loaded["access_token"] == mock_tokens["access_token"]


class TestOAuthFlow:
    """Test OAuth authorization flow."""
    
    def test_get_authorization_url(self):
        """Test building LinkedIn authorization URL."""
        auth = AuthManager()
        url = auth.get_authorization_url()
        
        assert "linkedin.com" in url
        assert "oauth/v2/authorization" in url
        assert "response_type=code" in url
        assert "client_id=" in url
        assert "redirect_uri=" in url
    
    @patch("linkedin_action_center.auth.manager.requests.post")
    def test_exchange_code_for_token_success(self, mock_post, tmp_path, mock_tokens):
        """Test successful code exchange."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_in": 5184000,
            "refresh_token_expires_in": 31536000,
        }
        mock_post.return_value = mock_response
        
        tokens_file = tmp_path / "tokens.json"
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            result = auth.exchange_code_for_token("auth_code_12345")
            
            assert "access_token" in result
            assert "access_token_expires_at" in result
            assert tokens_file.exists()
    
    @patch("linkedin_action_center.auth.manager.requests.post")
    def test_exchange_code_for_token_failure(self, mock_post, tmp_path):
        """Test failed code exchange raises AuthenticationError."""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "Invalid authorization code"
        mock_post.return_value = mock_response
        
        tokens_file = tmp_path / "tokens.json"
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            with pytest.raises(AuthenticationError):
                auth.exchange_code_for_token("invalid_code")


class TestTokenRefresh:
    """Test token refresh functionality."""
    
    @patch("linkedin_action_center.auth.manager.requests.post")
    def test_refresh_access_token_success(self, mock_post, tmp_path, mock_tokens):
        """Test successful token refresh."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "access_token": "refreshed_token",
            "expires_in": 5184000,
        }
        mock_post.return_value = mock_response
        
        tokens_file = tmp_path / "tokens.json"
        with open(tokens_file, "w") as f:
            json.dump(mock_tokens, f)
        
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            result = auth.refresh_access_token()
            
            assert result["access_token"] == "refreshed_token"
            assert "access_token_expires_at" in result
    
    def test_refresh_without_refresh_token(self, tmp_path):
        """Test refresh fails without refresh token."""
        tokens_file = tmp_path / "tokens.json"
        with open(tokens_file, "w") as f:
            json.dump({"access_token": "token"}, f)
        
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            with pytest.raises(AuthenticationError):
                auth.refresh_access_token()


class TestTokenAccess:
    """Test getting access tokens."""
    
    def test_get_access_token_when_valid(self, tmp_path, mock_tokens):
        """Test getting access token when it's still valid."""
        tokens_file = tmp_path / "tokens.json"
        with open(tokens_file, "w") as f:
            json.dump(mock_tokens, f)
        
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            token = auth.get_access_token()
            assert token == mock_tokens["access_token"]
    
    def test_get_access_token_without_auth(self, tmp_path):
        """Test getting token without authentication raises error."""
        tokens_file = tmp_path / "tokens.json"
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            with pytest.raises(AuthenticationError):
                auth.get_access_token()
    
    def test_is_authenticated_true(self, tmp_path, mock_tokens):
        """Test is_authenticated returns True with valid token."""
        tokens_file = tmp_path / "tokens.json"
        with open(tokens_file, "w") as f:
            json.dump(mock_tokens, f)
        
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            assert auth.is_authenticated() is True
    
    def test_is_authenticated_false(self, tmp_path):
        """Test is_authenticated returns False without token."""
        tokens_file = tmp_path / "tokens.json"
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            assert auth.is_authenticated() is False


class TestTokenStatus:
    """Test token status reporting."""
    
    def test_token_status_authenticated(self, tmp_path, mock_tokens):
        """Test token status when authenticated."""
        tokens_file = tmp_path / "tokens.json"
        with open(tokens_file, "w") as f:
            json.dump(mock_tokens, f)
        
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            status = auth.token_status()
            
            assert status["authenticated"] is True
            assert "access_token_days_remaining" in status
    
    def test_token_status_not_authenticated(self, tmp_path):
        """Test token status when not authenticated."""
        tokens_file = tmp_path / "tokens.json"
        with patch("linkedin_action_center.auth.manager.TOKENS_FILE", str(tokens_file)):
            auth = AuthManager()
            status = auth.token_status()
            
            assert status["authenticated"] is False
            assert "reason" in status
