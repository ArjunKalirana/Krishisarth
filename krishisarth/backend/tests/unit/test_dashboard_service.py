import pytest
from unittest.mock import MagicMock, patch
from influxdb_client.client.exceptions import InfluxDBError
from app.services.dashboard_service import get_farm_dashboard, get_moisture_status

@pytest.fixture
def mock_redis():
    with patch("app.services.dashboard_service.redis_client") as m:
        yield m

@pytest.fixture
def mock_influx():
    with patch("app.services.dashboard_service.query_influx") as m:
        yield m

def test_dashboard_returns_cached_data_if_fresh(mock_redis, mock_influx):
    mock_redis.get.return_value = '{"zones": [], "data_source": "cache"}'
    
    result = get_farm_dashboard("farm_1")
    
    assert result["data_source"] == "cache"
    mock_influx.assert_not_called()

def test_dashboard_queries_influxdb_on_cache_miss(mock_redis, mock_influx):
    mock_redis.get.return_value = None
    mock_influx.return_value = {"moisture": 45}
    
    result = get_farm_dashboard("farm_1")
    
    assert result["data_source"] == "live"
    mock_influx.assert_called_once()

def test_dashboard_returns_stale_cache_if_influxdb_down(mock_redis, mock_influx):
    mock_redis.get.side_effect = [None, '{"zones": [], "data_source": "stale"}']
    mock_influx.side_effect = ConnectionError("InfluxDB Down")
    
    result = get_farm_dashboard("farm_1")
    
    assert result["data_source"] == "stale"

def test_moisture_status_dry_below_25_percent():
    status = get_moisture_status(20)
    assert status == "DRY"

def test_moisture_status_wet_above_70_percent():
    status = get_moisture_status(85)
    assert status == "WET"

def test_moisture_status_ok_between_25_and_70():
    status = get_moisture_status(45)
    assert status == "OPTIMAL"
