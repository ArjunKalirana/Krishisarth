import uuid
import logging
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.irrigation_schedule import IrrigationSchedule
from app.models.fertigation_log import FertigationLog
from app.models.zone import Zone
from app.core.config import settings

# Safety Constraints
TANK_CRITICAL_PCT = 10.0
DEFAULT_FLOW_RATE_LPM = 10.0 # Placeholder for actual pump flow rate

logger = logging.getLogger(__name__)

async def start_irrigation(zone_id: str, duration_min: int, source: str, db: Session, redis) -> IrrigationSchedule:
    """
    Initiate irrigation for a specific zone.
    Enforces Redis-based pump locking and tank level safety checks.
    """
    # 1. Pump Safety Check: Direct Mutex via Redis
    lock_key = f"irrigation_lock:{zone_id}"
    if redis.get(lock_key):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="PUMP_ALREADY_RUNNING"
        )
        
    # 2. Environmental Safety Check: Prevent dry-run
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="ZONE_NOT_FOUND")
        
    farm_id = str(zone.farm_id)
    tank_level = redis.get(f"tank_level:{farm_id}")
    if tank_level and float(tank_level) < TANK_CRITICAL_PCT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="TANK_LEVEL_CRITICAL"
        )
        
    # 3. Persistence: Record the start of the event
    now = datetime.now(timezone.utc)
    schedule = IrrigationSchedule(
        zone_id=zone_id,
        scheduled_at=now,
        duration_min=duration_min,
        status="running",
        source=source
    )
    # Using dynamic attributes for started_at and estimated_end_at as requested in API response
    # These might need to be added to the model if persistence is required for them
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    # 4. Concurrency Control: Set Redis Lock with safety margin
    redis.setex(lock_key, duration_min * 60 + 60, "1")
    
    # 5. Execution: Enqueue to Celery (Background Worker)
    # Note: Using mock task ID as worker implementation is in next phase
    schedule.celery_task_id = f"task_{schedule.id}"
    db.commit()
    
    # Inject runtime fields for the response
    schedule.started_at = now
    schedule.estimated_end_at = now + timedelta(minutes=duration_min)
    
    return schedule

async def stop_irrigation(zone_id: str, db: Session, redis) -> dict:
    """
    Manually terminate a running irrigation session.
    Revokes background tasks and cleans up locks.
    """
    lock_key = f"irrigation_lock:{zone_id}"
    if not redis.get(lock_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PUMP_NOT_RUNNING"
        )
        
    # Load latest running schedule
    schedule = db.query(IrrigationSchedule).filter(
        IrrigationSchedule.zone_id == zone_id,
        IrrigationSchedule.status == "running"
    ).order_by(IrrigationSchedule.scheduled_at.desc()).first()
    
    if not schedule:
             raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PUMP_NOT_RUNNING"
        )
             
    # Cleanup background execution (Mock revocation)
    logger.info(f"Revoking Celery Task: {schedule.celery_task_id}")
    
    # Finalize record
    now = datetime.now(timezone.utc)
    actual_duration_sec = (now - schedule.scheduled_at).total_seconds()
    water_used_l = (actual_duration_sec / 60) * DEFAULT_FLOW_RATE_LPM
    
    schedule.status = "stopped_manually"
    schedule.executed_at = now
    # Note: If water_used_l is added to model, store it here
    db.commit()
    
    # Release Lock
    redis.delete(lock_key)
    
    return {
        "zone_id": zone_id,
        "pump_stopped": True,
        "water_used_l": round(water_used_l, 2),
        "stopped_at": now
    }

async def queue_fertigation(zone_id: str, nutrient_type: str, concentration_ml: float, db: Session, redis) -> FertigationLog:
    """
    Queue a nutrient injection. 
    Enforces that the pump must be running for injection to be valid.
    """
    lock_key = f"irrigation_lock:{zone_id}"
    if not redis.get(lock_key):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="PUMP_NOT_RUNNING"
        )
        
    log = FertigationLog(
        zone_id=zone_id,
        nutrient_type=nutrient_type,
        concentration_ml=concentration_ml,
        status="queued"
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    return log
