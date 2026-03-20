import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

def test_start_irrigation_returns_running_schedule(auth_headers):
    with patch("app.services.irrigation_service.get_tank_level", return_value=80):
        response = client.post(
            "/api/v1/zones/zone_1/irrigate",
            json={"duration_minutes": 15},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "RUNNING"

def test_start_irrigation_twice_returns_409_pump_already_running(auth_headers):
    with patch("app.services.irrigation_service.redis_client.exists", return_value=True):
        response = client.post(
            "/api/v1/zones/zone_1/irrigate",
            json={"duration_minutes": 10},
            headers=auth_headers
        )
        assert response.status_code == 409
        assert "PUMP_ALREADY_RUNNING" in response.json()["detail"]

def test_stop_irrigation_returns_water_used(auth_headers):
    with patch("app.services.irrigation_service.redis_client.get", return_value="zone_1"):
        with patch("app.services.irrigation_service.calculate_water_usage", return_value=45.2):
            response = client.post("/api/v1/zones/zone_1/stop", headers=auth_headers)
            assert response.status_code == 200
            assert response.json()["water_used_l"] == 45.2

def test_stop_irrigation_when_not_running_returns_400(auth_headers):
    with patch("app.services.irrigation_service.redis_client.get", return_value=None):
        response = client.post("/api/v1/zones/zone_1/stop", headers=auth_headers)
        assert response.status_code == 400

def test_fertigation_when_pump_not_running_returns_409(auth_headers):
    with patch("app.services.irrigation_service.redis_client.get", return_value=None):
        response = client.post(
            "/api/v1/zones/zone_1/fertigation",
            json={"nutrient_type": "Nitrogen", "concentration_ml_l": 10},
            headers=auth_headers
        )
        assert response.status_code == 409
        assert "PUMP_NOT_RUNNING" in response.json()["detail"]

def test_fertigation_above_20ml_returns_warning_in_response(auth_headers):
    with patch("app.services.irrigation_service.redis_client.get", return_value="zone_1"):
        response = client.post(
            "/api/v1/zones/zone_1/fertigation",
            json={"nutrient_type": "Nitrogen", "concentration_ml_l": 25},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "HIGH_CONCENTRATION_WARNING" in response.json()["warnings"]

def test_tank_critical_blocks_irrigation(auth_headers):
    with patch("app.services.irrigation_service.get_tank_level", return_value=5):
        response = client.post(
            "/api/v1/zones/zone_1/irrigate",
            json={"duration_minutes": 10},
            headers=auth_headers
        )
        assert response.status_code == 409
        assert "TANK_LEVEL_CRITICAL" in response.json()["detail"]
