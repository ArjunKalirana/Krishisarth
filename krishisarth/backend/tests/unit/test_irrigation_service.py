import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.services.irrigation_service import start_irrigation, stop_irrigation

@pytest.fixture
def mock_redis():
    with patch("app.services.irrigation_service.redis_client") as m:
        yield m

@pytest.fixture
def mock_celery():
    with patch("app.services.irrigation_service.celery_app") as m:
        yield m

def test_start_irrigation_sets_redis_lock(mock_redis, mock_celery):
    mock_redis.exists.return_value = False
    with patch("app.services.irrigation_service.get_tank_level", return_value=50):
        start_irrigation("zone_1", 20)
        mock_redis.set.assert_called_with("pump_lock_farm_1", "zone_1", ex=1200)

def test_start_irrigation_raises_409_if_lock_exists(mock_redis):
    mock_redis.exists.return_value = True
    with pytest.raises(HTTPException) as exc:
        start_irrigation("zone_1", 20)
    assert exc.value.status_code == 409
    assert "PUMP_ALREADY_RUNNING" in exc.value.detail

def test_start_irrigation_raises_409_if_tank_critical(mock_redis):
    mock_redis.exists.return_value = False
    with patch("app.services.irrigation_service.get_tank_level", return_value=5):
        with pytest.raises(HTTPException) as exc:
            start_irrigation("zone_1", 20)
        assert exc.value.status_code == 409
        assert "TANK_LEVEL_CRITICAL" in exc.value.detail

def test_stop_irrigation_deletes_redis_lock(mock_redis, mock_celery):
    mock_redis.get.return_value = "zone_1"
    stop_irrigation("zone_1")
    mock_redis.delete.assert_called_with("pump_lock_farm_1")

def test_stop_irrigation_raises_400_if_not_running(mock_redis):
    mock_redis.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        stop_irrigation("zone_1")
    assert exc.value.status_code == 400
    assert "PUMP_NOT_RUNNING" in exc.value.detail

def test_stop_irrigation_revokes_celery_task(mock_redis, mock_celery):
    mock_redis.get.return_value = "zone_1"
    mock_redis.hget.return_value = "task_uuid_123"
    stop_irrigation("zone_1")
    mock_celery.control.revoke.assert_called_once_with("task_uuid_123", terminate=True)
