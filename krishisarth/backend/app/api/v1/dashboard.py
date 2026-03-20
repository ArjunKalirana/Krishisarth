from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.db.postgres import get_db
from app.db.redis import get_redis
from app.db.influxdb import get_influx_client
from app.services import dashboard_service
from app.schemas.dashboard_schema import DashboardOut

router = APIRouter()

@router.get("/{farm_id}/dashboard", response_model=dict)
async def get_farm_dashboard(
    farm_id: str,
    db: Session = Depends(get_db),
    redis = Depends(get_redis),
    influx_client = Depends(get_influx_client),
    current_farmer = Depends(deps.get_current_farmer),
    # verify_farm_owner ensures the farmer has access to this farm_id
    _ = Depends(deps.verify_farm_owner)
) -> Any:
    """
    Get the comprehensive real-time dashboard for a farm.
    Aggregates PostgreSQL config, InfluxDB telemetry, and Redis cache.
    """
    try:
        data = await dashboard_service.get_dashboard(
            farm_id=farm_id,
            db=db,
            influx_client=influx_client,
            redis=redis
        )
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DASHBOARD_DATA_NOT_FOUND" # Should not happen if farm_id is valid
            )
            
        return {"success": True, "data": data}
        
    except Exception as e:
        # Graceful Failover: Check Redis for last known cache
        try:
            cached_data = redis.get(f"dashboard_cache:{farm_id}")
            if cached_data:
                import json
                data = json.loads(cached_data)
                data["data_source"] = "cache_emergency"
                return {"success": True, "data": data}
        except Exception:
            pass
            
        # If Redis also fails or has no data, return 503
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TELEMETRY_SERVICE_UNAVAILABLE"
        )
