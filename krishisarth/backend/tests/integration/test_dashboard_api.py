import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

def test_dashboard_returns_all_required_fields(auth_headers):
    with patch("app.services.dashboard_service.redis_client.get", return_value=None):
        with patch("app.services.dashboard_service.query_influx", return_value={"moisture": 45}):
            response = client.get("/api/v1/farms/farm_1/dashboard", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert "zones" in data
            assert data["data_source"] == "live"

def test_dashboard_returns_stale_cache_notice_when_influxdb_down(auth_headers):
    # Mock cache hit for stale data and InfluxDB failure
    stale_data = '{"summary": {"status": "OFFLINE"}, "zones": [], "data_source": "stale"}'
    with patch("app.services.dashboard_service.redis_client.get", side_effect=[None, stale_data]):
        with patch("app.services.dashboard_service.query_influx", side_effect=ConnectionError()):
            response = client.get("/api/v1/farms/farm_1/dashboard", headers=auth_headers)
            assert response.status_code == 200
            assert response.json()["data_source"] == "stale"
