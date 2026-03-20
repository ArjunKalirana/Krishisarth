import pytest
from unittest.mock import MagicMock, patch
from app.services.sensor_service import validate_readings
from app.models.alert import AlertSeverity

def test_moisture_above_100_is_rejected():
    with patch("app.services.alert_service.create_alert") as mock_alert:
        readings = {"moisture": 105.5}
        valid, rejected = validate_readings("zone_1", readings)
        
        assert valid == {}
        assert "moisture" in rejected
        mock_alert.assert_called_once()
        assert mock_alert.call_args[0][2] == AlertSeverity.CRITICAL

def test_moisture_below_0_is_rejected():
    readings = {"moisture": -5.0}
    valid, rejected = validate_readings("zone_1", readings)
    assert valid == {}
    assert "moisture" in rejected

def test_temp_above_60_is_rejected():
    readings = {"temperature": 65.0}
    valid, rejected = validate_readings("zone_1", readings)
    assert "temperature" in rejected

def test_ph_above_14_is_rejected():
    readings = {"ph": 15.0}
    valid, rejected = validate_readings("zone_1", readings)
    assert "ph" in rejected

def test_all_valid_readings_are_accepted():
    readings = {"moisture": 45.0, "temperature": 28.5, "ph": 6.8}
    valid, rejected = validate_readings("zone_1", readings)
    assert len(valid) == 3
    assert len(rejected) == 0

def test_rejected_reading_generates_sensor_fault_alert():
    with patch("app.services.alert_service.create_alert") as mock_alert:
        validate_readings("zone_1", {"moisture": 200})
        mock_alert.assert_called_once()
        assert "SENSOR_FAULT" in mock_alert.call_args[0][1]
