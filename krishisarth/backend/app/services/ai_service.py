import json
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.ai_decision import AIDecision
from app.models.zone import Zone
from app.core import constants
from app.db.influxdb import get_query_api
from app.db.redis import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class ModelLoadError(Exception):
    """Raised when machine learning models fail to initialize."""
    pass

async def run_inference(zone_id: str, db: Session) -> AIDecision:
    """
    Execute an AI reasoning cycle for a zone.
    Fallback Logic: ML Model (LSTM+RF) -> Rule-Based Fallback.
    """
    redis = next(get_redis())
    query_api = get_query_api()
    bucket = settings.INFLUXDB_BUCKET
    
    # 1. Input Collection: Create a high-fidelity environment snapshot
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise ValueError("ZONE_NOT_FOUND")
        
    farm_id = str(zone.farm_id)
    
    # Fetch latest moisture from InfluxDB (last 24h)
    moisture_pct = 0.0
    try:
        flux = f'''
        from(bucket: "{bucket}")
          |> range(start: -24h)
          |> filter(fn: (r) => r["_measurement"] == "soil_readings")
          |> filter(fn: (r) => r["zone_id"] == "{zone_id}")
          |> last()
        '''
        results = query_api.query(flux)
        for table in results:
            for record in table.records:
                if record.get_field() == "moisture":
                    moisture_pct = record.get_value()
    except Exception as e:
        logger.error(f"Telemetry Fetch Failure: {str(e)}")

    tank_level = redis.get(f"tank_level:{farm_id}")
    tank_val = float(tank_level) if tank_level else 100.0
    
    snapshot = {
        "moisture_pct": moisture_pct,
        "crop_type": zone.crop_type,
        "crop_stage": zone.crop_stage,
        "tank_level": tank_val,
        "at": datetime.now(timezone.utc).isoformat()
    }
    
    # 2. Reasoning Chain: Fallback Implementation
    decision_type = "skip"
    confidence = 0.5
    reasoning = "Steady state moisture levels."
    
    # ML Prediction Block (Stubbed for future weights)
    # try:
    #     ml_result = some_ml_lib.predict(snapshot)
    # except Exception:
    #     logger.warning("ML Inference failure. Reverting to Rule-Based fallback.")
    
    # Safety Rule Fallback: Moisture < 25% (PROJECT_RULES.md 5.9)
    if moisture_pct < constants.AI_MOISTURE_RULE_THRESHOLD * 100:
        decision_type = "irrigate"
        confidence = 1.0 # Rules are explicit safety overrides
        reasoning = f"Moisture drop detected ({moisture_pct}%). Threshold triggered."

    # 3. Decision Persistence
    decision = AIDecision(
        zone_id=zone_id,
        decision_type=decision_type,
        reasoning=reasoning,
        confidence=confidence,
        input_snapshot=snapshot,
        water_saved_l=0.0 # To be calculated after irrigation
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    
    # 4. Trigger Action (If Confidence >= Threshold)
    if confidence >= constants.AI_AUTO_EXECUTE_THRESHOLD:
        # Note: In production, this would trigger irrigation_service.start_irrigation
        logger.info(f"AI AUTO_EXECUTE Triggered: Zone {zone_id} ({decision_type})")
        
    return decision
