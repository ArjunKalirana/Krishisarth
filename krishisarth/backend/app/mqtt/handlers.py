import json
import logging
import asyncio
from datetime import datetime, timezone
from influxdb_client import Point
from app.db.influxdb import get_write_api
from app.db.postgres import SessionLocal
from app.db.redis import get_redis
from app.models.alert import Alert
from app.core.config import settings

logger = logging.getLogger(__name__)

# Sensor Validity Bounds (PROJECT_RULES.md 5.8)
BOUNDS = {
    "moisture_pct": (0.0, 100.0),
    "temp_c": (-10.0, 60.0),
    "ec_ds_m": (0.0, 10.0),
    "ph": (0.0, 14.0),
    "humidity_pct": (0.0, 100.0),
    "pressure_bar": (0.0, 10.0)
}

def validate_telemetry(payload: dict, fields: list) -> bool:
    """Validate all required fields against known physical bounds."""
    for field in fields:
        if field not in payload:
            return False
        val = payload[field]
        low, high = BOUNDS.get(field, (float('-inf'), float('inf')))
        if not (low <= val <= high):
            logger.warning(f"SENSOR_OUT_OF_BOUNDS: {field}={val} (Allowed: {low}-{high})")
            return False
    return True

async def handle_soil_reading(zone_id: str, payload: dict):
    """Process and persist soil sensor data."""
    required = ["moisture_pct", "temp_c", "ec_ds_m", "ph"]
    if not validate_telemetry(payload, required):
        # Trigger Sensor Fault Alert
        _create_sensor_alert(zone_id, "soil_sensor_fault", f"Invalid soil reading: {payload}")
        return

    write_api = get_write_api()
    point = Point("soil_readings") \
        .tag("zone_id", zone_id) \
        .tag("device_id", payload.get("device_id", "unknown")) \
        .tag("depth_cm", payload.get("depth_cm", "0")) \
        .field("moisture", float(payload["moisture_pct"])) \
        .field("temp_c", float(payload["temp_c"])) \
        .field("ec_ds_m", float(payload["ec_ds_m"])) \
        .field("ph", float(payload["ph"])) \
        .time(datetime.now(timezone.utc))
    
    write_api.write(bucket=settings.INFLUXDB_BUCKET, record=point)

async def handle_ambient_reading(zone_id: str, payload: dict):
    """Process and persist ambient air data."""
    required = ["temp_c", "humidity_pct"]
    if not validate_telemetry(payload, required):
        _create_sensor_alert(zone_id, "ambient_sensor_fault", f"Invalid ambient reading: {payload}")
        return

    write_api = get_write_api()
    point = Point("ambient_readings") \
        .tag("zone_id", zone_id) \
        .field("temp_c", float(payload["temp_c"])) \
        .field("humidity", float(payload["humidity_pct"])) \
        .time(datetime.now(timezone.utc))
    
    write_api.write(bucket=settings.INFLUXDB_BUCKET, record=point)

async def handle_pump_telemetry(zone_id: str, payload: dict):
    """Process and monitor pump hardware performance."""
    required = ["pressure_bar", "flow_lpm", "is_running"]
    if not validate_telemetry(payload, ["pressure_bar"]):
        return

    write_api = get_write_api()
    point = Point("pump_telemetry") \
        .tag("zone_id", zone_id) \
        .field("pressure", float(payload["pressure_bar"])) \
        .field("flow_rate", float(payload.get("flow_lpm", 0.0))) \
        .field("is_running", bool(payload["is_running"])) \
        .time(datetime.now(timezone.utc))
    
    write_api.write(bucket=settings.INFLUXDB_BUCKET, record=point)
    
    # Check for pressure drop (>0.4 bar) - can be offloaded to alert_worker
    if payload.get("pressure_drop_detected", False):
        _create_sensor_alert(zone_id, "pressure_drop", "Critical pressure drop detected in zone main-line.")

def _create_sensor_alert(zone_id: str, alert_type: str, message: str):
    """Internal helper to log alerts in PostgreSQL."""
    db = SessionLocal()
    try:
        alert = Alert(
            zone_id=zone_id,
            severity="warning",
            alert_type=alert_type,
            message=message,
            is_read=False
        )
        db.add(alert)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to record sensor alert: {str(e)}")
    finally:
        db.close()
