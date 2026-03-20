import pytest
from unittest.mock import MagicMock, patch
from app.services.ai_service import run_inference
from app.models.ai_decision import ExecutionMode

@pytest.fixture
def mock_model():
    with patch("app.services.ai_service.agri_brain_model") as m:
        yield m

def test_run_inference_auto_executes_above_threshold(mock_model):
    mock_model.predict.return_value = {"confidence": 0.85, "recommendation": "IRRIGATE"}
    
    decision = run_inference("zone_1")
    
    assert decision.mode == ExecutionMode.AUTONOMOUS
    assert decision.confidence == 0.85

def test_run_inference_flags_manual_review_at_medium_confidence(mock_model):
    mock_model.predict.return_value = {"confidence": 0.70, "recommendation": "STABILIZE"}
    
    decision = run_inference("zone_1")
    
    assert decision.mode == ExecutionMode.MANUAL_REVIEW

def test_run_inference_saves_informational_below_threshold(mock_model):
    mock_model.predict.return_value = {"confidence": 0.50, "recommendation": "NONE"}
    
    decision = run_inference("zone_1")
    
    assert decision.severity == "INFORMATIONAL"

def test_run_inference_uses_rule_based_fallback_on_model_error(mock_model):
    mock_model.predict.side_effect = Exception("Model Timeout")
    
    with patch("app.services.ai_service.rule_engine_fallback") as mock_fallback:
        run_inference("zone_1")
        mock_fallback.assert_called_once()

def test_run_inference_uses_zero_rain_probability_when_weather_unavailable():
    with patch("app.services.weather_service.get_forecast", side_effect=ConnectionError()):
        decision = run_inference("zone_1")
        assert "rain_prob: 0" in decision.reasoning

def test_input_snapshot_is_saved_with_decision(mock_model):
    mock_model.predict.return_value = {"confidence": 0.9, "recommendation": "OK"}
    with patch("app.services.sensor_service.get_latest_readings", return_value={"moisture": 40}):
        decision = run_inference("zone_1")
        assert decision.sensor_snapshot["moisture"] == 40
