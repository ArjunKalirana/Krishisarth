import json
from datetime import datetime, timezone, date, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Zone, Device, Alert, AIDecision
from app.core.config import settings

def get_moisture_status(pct: float) -> str:
    """Categorize moisture percentage into Dry/OK/Wet."""
    if pct < 25:
        return "dry"
    if pct > 70:
        return "wet"
    return "ok"

async def get_dashboard(farm_id: str, db: Session, influx_client, redis) -> dict:
    """
    Main aggregator for farm dashboard data.
    Uses Redis caching with 60s TTL.
    """
    cache_key = f"dashboard_cache:{farm_id}"
    
    # --- Step 1: Redis Cache Check ---
    try:
        cached_data = redis.get(cache_key)
        if cached_data:
            data = json.loads(cached_data)
            data["data_source"] = "cache"
            return data
    except Exception:
        pass # Redis unavailable, proceed to live query

    # --- Step 2: PostgreSQL Data Collection ---
    zones = db.query(Zone).filter(Zone.farm_id == farm_id).all()
    if not zones:
        return None # Farm not found or empty
    
    zone_map = {str(z.id): z.name for z in zones}
    active_count = sum(1 for z in zones if z.is_active)
    
    devices = db.query(Device).filter(Device.farm_id == farm_id).all()
    offline_count = sum(1 for d in devices if not d.is_online)
    
    unread_count = db.query(Alert).join(Zone).filter(
        Zone.farm_id == farm_id, 
        Alert.is_read == False
    ).count()
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    water_saved = db.query(func.sum(AIDecision.water_saved_l)).filter(
        AIDecision.farm_id == farm_id,
        AIDecision.created_at >= today_start
    ).scalar() or 0.0

    # --- Step 3: InfluxDB Telemetry (Flux Queries) ---
    query_api = influx_client.query_api()
    bucket = settings.INFLUXDB_BUCKET
    
    # 3.1: Latest Soil Moisture/Temp/EC per Zone
    zone_ids_filter = '", "'.join(zone_map.keys())
    flux_soil = f'''
    from(bucket: "{bucket}")
      |> range(start: -24h)
      |> filter(fn: (r) => r["_measurement"] == "soil_readings")
      |> filter(fn: (r) => contains(value: r["zone_id"], set: ["{zone_ids_filter}"]))
      |> last()
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    
    # 3.2: Latest Water Quality
    flux_wq = f'''
    from(bucket: "{bucket}")
      |> range(start: -24h)
      |> filter(fn: (r) => r["_measurement"] == "water_quality")
      |> filter(fn: (r) => r["farm_id"] == "{farm_id}")
      |> last()
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''

    # Initial Dashboard Structure
    dashboard = {
        "summary": {
            "water_saved_today_l": float(water_saved),
            "system_status": "optimal" if offline_count == 0 else "degraded",
            "next_irrigation_at": None, # Future AI logic
            "active_zones": active_count,
            "offline_devices": offline_count
        },
        "zones": [],
        "water_quality": {
            "ph": None, "ec_ms_cm": None, "turbidity_ntu": None, "nitrate_ppm": None
        },
        "tank_level_pct": 0.0,
        "unread_alerts": unread_count,
        "data_source": "live"
    }

    # Process Soil Telemetry
    soil_results = query_api.query(flux_soil)
    soil_data = {}
    for table in soil_results:
        for record in table.records:
            zid = record.values.get("zone_id")
            soil_data[zid] = {
                "moisture": record.values.get("moisture", 0.0),
                "temp_c": record.values.get("temp_c"),
                "ec_ds_m": record.values.get("ec_ds_m")
            }

    # Build Zone list with statuses
    for zid, name in zone_map.items():
        telemetry = soil_data.get(zid, {"moisture": 0.0, "temp_c": None, "ec_ds_m": None})
        dashboard["zones"].append({
            "id": zid,
            "name": name,
            "moisture_pct": telemetry["moisture"],
            "moisture_status": get_moisture_status(telemetry["moisture"]),
            "temp_c": telemetry.get("temp_c"),
            "ec_ds_m": telemetry.get("ec_ds_m"),
            "pump_running": False # Telemetry integration point
        })

    # Process Water Quality
    wq_results = query_api.query(flux_wq)
    for table in wq_results:
        for record in table.records:
            dashboard["water_quality"] = {
                "ph": record.values.get("ph"),
                "ec_ms_cm": record.values.get("ec_ms_cm"),
                "turbidity_ntu": record.values.get("turbidity_ntu"),
                "nitrate_ppm": record.values.get("nitrate_ppm")
            }
            if "tank_level" in record.values:
                dashboard["tank_level_pct"] = record.values.get("tank_level")

    # --- Step 4: Redis Cache Update ---
    try:
        redis.setex(cache_key, 60, json.dumps(dashboard, default=str))
    except Exception:
        pass

    return dashboard
