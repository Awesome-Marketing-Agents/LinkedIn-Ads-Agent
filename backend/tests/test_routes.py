"""Integration tests for API routes using TestClient."""

from unittest.mock import patch

import pytest


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")


def test_report_campaign_metrics_empty(client):
    response = client.get("/api/v1/report/campaign-metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["rows"] == []
    assert data["total"] == 0


def test_report_creative_metrics_empty(client):
    response = client.get("/api/v1/report/creative-metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["rows"] == []
    assert data["total"] == 0


def test_report_demographics_empty(client):
    response = client.get("/api/v1/report/demographics")
    assert response.status_code == 200
    data = response.json()
    assert data["rows"] == []


def test_report_visual_empty(client):
    response = client.get("/api/v1/report/visual")
    assert response.status_code == 200
    data = response.json()
    assert "time_series" in data
    assert "kpis" in data


def test_report_accounts_empty(client):
    response = client.get("/api/v1/report/accounts")
    assert response.status_code == 200
    data = response.json()
    assert data["rows"] == []


def test_report_campaigns_empty(client):
    response = client.get("/api/v1/report/campaigns")
    assert response.status_code == 200
    data = response.json()
    assert data["rows"] == []


def test_auth_status(client):
    with patch("app.core.deps.get_auth") as mock:
        mock_auth = mock.return_value
        mock_auth.token_status.return_value = {"authenticated": False, "reason": "No tokens"}
        response = client.get("/api/v1/auth/status")
        assert response.status_code == 200
