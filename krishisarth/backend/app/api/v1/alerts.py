from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.db.postgres import get_db
from app.services import alert_service
from app.schemas.alert_schema import AlertOut

router = APIRouter()

@router.get("/farms/{farm_id}/alerts", response_model=dict)
def list_farm_alerts(
    farm_id: str,
    is_read: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_farmer = Depends(deps.get_current_farmer),
    # verify_farm_owner ensures the access is valid
    _ = Depends(deps.verify_farm_owner)
) -> Any:
    """
    Get a list of notifications for the specified farm.
    Includes filtering by read status and severity levels.
    """
    alerts, unread_count = alert_service.get_alerts(
        farm_id=farm_id, 
        db=db, 
        is_read=is_read, 
        severity=severity, 
        limit=limit
    )
    
    return {
        "success": True,
        "data": {
            "alerts": [AlertOut.model_validate(a) for a in alerts],
            "unread_count": unread_count
        }
    }

@router.patch("/{alert_id}/read", response_model=dict)
def mark_alert_as_read(
    alert_id: str,
    db: Session = Depends(get_db),
    current_farmer = Depends(deps.get_current_farmer)
) -> Any:
    """
    Mark a specific alert as acknowledged by the farmer.
    Returns 403 if the farmer attempt to access an alert from another farm.
    """
    alert = alert_service.mark_read(alert_id, current_farmer.id, db)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ALERT_ACCESS_DENIED"
        )
        
    return {
        "success": True, 
        "data": AlertOut.model_validate(alert)
    }
