import csv
import io
from datetime import date, datetime, timezone
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.api import deps
from app.db.postgres import get_db
from app.models.fertigation_log import FertigationLog
from app.models.zone import Zone

router = APIRouter()

@router.get("/{farm_id}/analytics", response_model=dict)
def get_farm_analytics_summary(
    farm_id: str,
    from_date: date = Query(...),
    to_date: date = Query(...),
    zone_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_farmer = Depends(deps.get_current_farmer),
    _ = Depends(deps.verify_farm_owner)
) -> Any:
    """Historical data aggregation for farm operations."""
    # Safety Check: Limit range to prevent DOS (90 Days max)
    if (to_date - from_date).days > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_DATE_RANGE"
        )
    
    return {
        "success": True,
        "data": {
            "range": {"from": from_date, "to": to_date},
            "summary": {"total_water_liters": 0, "nutrient_cycles": 0},
            "details": "Aggregation logic pending InfluxDB integration"
        }
    }

@router.get("/{farm_id}/analytics/export")
def stream_fertigation_csv(
    farm_id: str,
    db: Session = Depends(get_db),
    current_farmer = Depends(deps.get_current_farmer),
    _ = Depends(deps.verify_farm_owner)
) -> Any:
    """
    Stream a CSV export of all fertigation (nutrient) logs for a farm.
    Memory-efficient implementation using Python generators.
    """
    # Build logs query joining with Zone to verify farm ownership
    logs = db.query(FertigationLog).join(Zone).filter(Zone.farm_id == farm_id).all()
    
    def generate_csv_rows():
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["entry_id", "zone_name", "nutrient", "concentration_ml", "applied_at"])
        yield output.getvalue()
        output.truncate(0)
        output.seek(0)
        
        # Body
        for log in logs:
            writer.writerow([
                str(log.id),
                log.zone.name,
                log.nutrient_type,
                log.concentration_ml,
                log.applied_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            ])
            yield output.getvalue()
            output.truncate(0)
            output.seek(0)

    filename = f"krishisarth-logs-{date.today()}.csv"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return StreamingResponse(generate_csv_rows(), media_type="text/csv", headers=headers)
