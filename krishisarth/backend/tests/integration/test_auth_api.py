import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

def test_register_success(client: TestClient):
    response = client.post(
        "/v1/auth/register",
        json={
            "name": "New Farmer",
            "email": "fresh@krishisarth.test",
            "password": "StrongPassword123",
            "phone": "+919998887776"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["email"] == "fresh@krishisarth.test"

def test_register_duplicate_email_returns_409(client: TestClient, test_farmer):
    response = client.post(
        "/v1/auth/register",
        json={
            "name": "Another User",
            "email": test_farmer.email,
            "password": "Password123"
        }
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"

def test_login_success_returns_tokens(client: TestClient, test_farmer):
    response = client.post(
        "/v1/auth/login",
        json={
            "email": test_farmer.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]

def test_login_wrong_password_never_reveals_field(client: TestClient, test_farmer):
    response = client.post(
        "/v1/auth/login",
        json={
            "email": test_farmer.email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    # PROJECT_RULES.md 5.3 + Security Requirement: Must not reveal which field is wrong
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"

@pytest.mark.asyncio
async def test_refresh_token_rotation_works(client: TestClient, test_farmer, mock_redis):
    # Setup mock for successful rotation
    mock_redis.get.return_value = None
    
    # login first to get refresh token is one way, but we can just use auth_service
    from app.services import auth_service
    rf_token, _ = auth_service.create_refresh_token(test_farmer.id)
    
    response = client.post(
        "/v1/auth/refresh",
        json={"refresh_token": rf_token}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
    assert "refresh_token" in response.json()["data"]

def test_rate_limit_returns_429_after_100_requests(client: TestClient, mock_redis):
    # Simulate 101st request
    mock_redis.incr.return_value = 101
    
    # Any request with a Bearer token fragment will trigger the limit
    headers = {"Authorization": "Bearer some_long_test_token_string"}
    response = client.get("/v1/auth/logout", headers=headers) # Mocked logout route
    
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert response.headers["Retry-After"] == "60"
