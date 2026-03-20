import pytest
from unittest.mock import MagicMock
from jose import jwt
from fastapi import HTTPException
from app.services import auth_service
from app.core.config import settings

def test_hash_password_produces_different_hashes_each_time():
    pw = "secret_password"
    h1 = auth_service.hash_password(pw)
    h2 = auth_service.hash_password(pw)
    assert h1 != h2
    assert auth_service.verify_password(pw, h1)
    assert auth_service.verify_password(pw, h2)

def test_verify_password_correct():
    pw = "secure123"
    hashed = auth_service.hash_password(pw)
    assert auth_service.verify_password(pw, hashed) is True

def test_verify_password_wrong():
    hashed = auth_service.hash_password("secure123")
    assert auth_service.verify_password("wrong_password", hashed) is False

def test_create_access_token_contains_farmer_id():
    fid = "550e8400-e29b-41d4-a716-446655440000"
    token = auth_service.create_access_token(fid)
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    assert payload["farmer_id"] == fid
    assert payload["sub"] == "access"

def test_create_refresh_token_returns_unique_jti():
    fid = "550e8400-e29b-41d4-a716-446655440000"
    token1, jti1 = auth_service.create_refresh_token(fid)
    token2, jti2 = auth_service.create_refresh_token(fid)
    assert jti1 != jti2
    assert token1 != token2

@pytest.mark.asyncio
async def test_rotate_refresh_token_revokes_old_jti():
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    
    fid = "test_fid"
    token, jti = auth_service.create_refresh_token(fid)
    
    new_acc, new_ref, out_fid = await auth_service.rotate_refresh_token(token, mock_redis)
    
    assert out_fid == fid
    # Ensure JTI was added to denylist in Redis
    mock_redis.setex.assert_called()
    call_key = mock_redis.setex.call_args[0][0]
    assert f"revoked_jti:{jti}" == call_key

@pytest.mark.asyncio
async def test_rotate_refresh_token_raises_on_reused_jti():
    mock_redis = MagicMock()
    mock_redis.get.return_value = b"1" # JTI exists in denylist
    
    token, _ = auth_service.create_refresh_token("fid")
    
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.rotate_refresh_token(token, mock_redis)
    
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "TOKEN_REUSED"

@pytest.mark.asyncio
async def test_brute_force_raises_429_when_locked():
    mock_redis = MagicMock()
    mock_redis.get.return_value = b"1"
    
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.check_brute_force("bad@actor.com", mock_redis)
        
    assert excinfo.value.status_code == 429
    assert excinfo.value.detail == "ACCOUNT_LOCKED"
