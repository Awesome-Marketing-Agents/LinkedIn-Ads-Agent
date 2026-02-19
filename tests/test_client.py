"""Unit tests for LinkedInClient."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from linkedin_action_center.ingestion.client import LinkedInClient
from linkedin_action_center.utils.errors import LinkedInAPIError, RateLimitError


class TestLinkedInClientInit:
    """Test LinkedInClient initialization."""
    
    def test_init_with_auth_manager(self, mock_auth_manager):
        """Test creating client with AuthManager."""
        client = LinkedInClient(mock_auth_manager)
        assert client._auth == mock_auth_manager
    
    def test_headers_include_authorization(self, mock_auth_manager):
        """Test that headers include proper authorization."""
        client = LinkedInClient(mock_auth_manager)
        headers = client._headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")
        assert "LinkedIn-Version" in headers
        assert "X-Restli-Protocol-Version" in headers


class TestHTTPMethods:
    """Test HTTP method wrappers."""
    
    @patch("linkedin_action_center.ingestion.client.requests.get")
    def test_get_success(self, mock_get, mock_auth_manager, mock_response):
        """Test successful GET request."""
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response
        
        client = LinkedInClient(mock_auth_manager)
        result = client.get("/campaigns")
        
        assert result == {"data": "test"}
        mock_get.assert_called_once()
    
    @patch("linkedin_action_center.ingestion.client.requests.get")
    def test_get_with_params(self, mock_get, mock_auth_manager, mock_response):
        """Test GET request with query parameters."""
        mock_get.return_value = mock_response
        
        client = LinkedInClient(mock_auth_manager)
        client.get("/campaigns", "status=ACTIVE")
        
        # Verify URL includes params
        called_url = mock_get.call_args[0][0]
        assert "status=ACTIVE" in called_url
    
    @patch("linkedin_action_center.ingestion.client.requests.get")
    def test_get_rate_limit_error(self, mock_get, mock_auth_manager):
        """Test GET request handles 429 rate limit."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_get.return_value = mock_response
        
        client = LinkedInClient(mock_auth_manager)
        with pytest.raises(RateLimitError) as exc_info:
            client.get("/campaigns")
        
        assert exc_info.value.retry_after == 60
    
    @patch("linkedin_action_center.ingestion.client.requests.get")
    def test_get_api_error(self, mock_get, mock_auth_manager):
        """Test GET request handles general API errors."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Server error"
        mock_response.headers = {"content-type": "text/plain"}
        mock_get.return_value = mock_response
        
        client = LinkedInClient(mock_auth_manager)
        with pytest.raises(LinkedInAPIError) as exc_info:
            client.get("/campaigns")
        
        assert exc_info.value.status_code == 500


class TestPagination:
    """Test pagination handling."""
    
    @patch("linkedin_action_center.ingestion.client.requests.get")
    def test_get_all_pages_single_page(self, mock_get, mock_auth_manager, mock_response):
        """Test pagination with single page of results."""
        mock_response.json.return_value = {
            "elements": [{"id": 1}, {"id": 2}],
            "metadata": {}
        }
        mock_get.return_value = mock_response
        
        client = LinkedInClient(mock_auth_manager)
        results = client.get_all_pages("/campaigns")
        
        assert len(results) == 2
        assert results[0]["id"] == 1
    
    @patch("linkedin_action_center.ingestion.client.requests.get")
    def test_get_all_pages_multiple_pages_offset(self, mock_get, mock_auth_manager):
        """Test offset-based pagination across multiple pages."""
        # First page
        response1 = MagicMock()
        response1.ok = True
        response1.status_code = 200
        response1.json.return_value = {
            "elements": [{"id": i} for i in range(100)],
            "metadata": {}
        }
        
        # Second page (less than page_size, so it's the last page)
        response2 = MagicMock()
        response2.ok = True
        response2.status_code = 200
        response2.json.return_value = {
            "elements": [{"id": i} for i in range(100, 150)],
            "metadata": {}
        }
        
        mock_get.side_effect = [response1, response2]
        
        client = LinkedInClient(mock_auth_manager)
        results = client.get_all_pages("/campaigns", page_size=100)
        
        assert len(results) == 150
        assert mock_get.call_count == 2
    
    @patch("linkedin_action_center.ingestion.client.requests.get")
    def test_get_all_pages_token_based(self, mock_get, mock_auth_manager):
        """Test token-based pagination."""
        # First page with next token
        response1 = MagicMock()
        response1.ok = True
        response1.status_code = 200
        response1.json.return_value = {
            "elements": [{"id": 1}, {"id": 2}],
            "metadata": {"nextPageToken": "token123"}
        }
        
        # Second page without next token
        response2 = MagicMock()
        response2.ok = True
        response2.status_code = 200
        response2.json.return_value = {
            "elements": [{"id": 3}, {"id": 4}],
            "metadata": {}
        }
        
        mock_get.side_effect = [response1, response2]
        
        client = LinkedInClient(mock_auth_manager)
        results = client.get_all_pages("/campaigns")
        
        assert len(results) == 4
        assert mock_get.call_count == 2
        
        # Verify second call used pageToken
        second_call_url = mock_get.call_args_list[1][0][0]
        assert "pageToken=token123" in second_call_url
    
    @patch("linkedin_action_center.ingestion.client.requests.get")
    def test_get_all_pages_custom_key(self, mock_get, mock_auth_manager, mock_response):
        """Test pagination with custom response key."""
        mock_response.json.return_value = {
            "items": [{"id": 1}, {"id": 2}],
            "metadata": {}
        }
        mock_get.return_value = mock_response
        
        client = LinkedInClient(mock_auth_manager)
        results = client.get_all_pages("/custom", key="items")
        
        assert len(results) == 2
    
    @patch("linkedin_action_center.ingestion.client.requests.get")
    def test_get_all_pages_empty_response(self, mock_get, mock_auth_manager, mock_response):
        """Test pagination with empty results."""
        mock_response.json.return_value = {
            "elements": [],
            "metadata": {}
        }
        mock_get.return_value = mock_response
        
        client = LinkedInClient(mock_auth_manager)
        results = client.get_all_pages("/campaigns")
        
        assert len(results) == 0
        assert isinstance(results, list)


class TestErrorHandling:
    """Test error handling in HTTP operations."""
    
    @patch("linkedin_action_center.ingestion.client.requests.get")
    def test_handles_network_errors(self, mock_get, mock_auth_manager):
        """Test handling of network-level errors."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Network unreachable")
        
        client = LinkedInClient(mock_auth_manager)
        with pytest.raises(requests.ConnectionError):
            client.get("/campaigns")
    
    @patch("linkedin_action_center.ingestion.client.requests.get")
    def test_handles_json_decode_errors(self, mock_get, mock_auth_manager):
        """Test handling of invalid JSON responses."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        client = LinkedInClient(mock_auth_manager)
        with pytest.raises(ValueError):
            client.get("/campaigns")
