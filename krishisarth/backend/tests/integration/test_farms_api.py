import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_farm_returns_201(auth_headers):
    response = client.post(
        "/api/v1/farms",
        json={"name": "Alpha Orchard", "location": "Nagpur, MH"},
        headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Alpha Orchard"

def test_create_farm_requires_auth_returns_401():
    response = client.post("/api/v1/farms", json={"name": "No Auth Farm"})
    assert response.status_code == 401

def test_list_farms_returns_only_own_farms(auth_headers, second_auth_headers):
    # Farmer 1 creates a farm
    client.post("/api/v1/farms", json={"name": "Farmer 1 Farm"}, headers=auth_headers)
    
    # Farmer 2 creates a farm
    client.post("/api/v1/farms", json={"name": "Farmer 2 Farm"}, headers=second_auth_headers)
    
    # Farmer 1 list
    response = client.get("/api/v1/farms", headers=auth_headers)
    farms = response.json()
    assert len(farms) == 1
    assert farms[0]["name"] == "Farmer 1 Farm"

def test_get_farm_by_id_returns_404_for_nonexistent(auth_headers):
    response = client.get("/api/v1/farms/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert response.status_code == 404

def test_get_another_farmers_farm_returns_403_not_404(auth_headers, second_auth_headers):
    # Farmer 2 creates a farm
    res = client.post("/api/v1/farms", json={"name": "Secret Garden"}, headers=second_auth_headers)
    farm_id = res.json()["id"]
    
    # Farmer 1 tries to access it
    response = client.get(f"/api/v1/farms/{farm_id}", headers=auth_headers)
    assert response.status_code == 403 

def test_create_zone_success(auth_headers):
    res = client.post("/api/v1/farms", json={"name": "Zone Farm"}, headers=auth_headers)
    farm_id = res.json()["id"]
    
    response = client.post(
        f"/api/v1/farms/{farm_id}/zones",
        json={"name": "Tomato Block A", "crop_type": "Tomato"},
        headers=auth_headers
    )
    assert response.status_code == 201

def test_patch_zone_crop_stage(auth_headers):
    # Setup zone
    res_farm = client.post("/api/v1/farms", json={"name": "Patch Farm"}, headers=auth_headers)
    res_zone = client.post(f"/api/v1/farms/{res_farm.json()['id']}/zones", json={"name": "Z1"}, headers=auth_headers)
    zone_id = res_zone.json()["id"]
    
    response = client.patch(
        f"/api/v1/zones/{zone_id}",
        json={"crop_stage": "FLOWERING"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["crop_stage"] == "FLOWERING"
