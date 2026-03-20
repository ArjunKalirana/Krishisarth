import logging
from datetime import datetime, timezone, timedelta
from app.workers.celery_app import app
from app.db.postgres import SessionLocal
from app.db.redis import get_redis
from app.models.irrigation_schedule import IrrigationSchedule
from app.models.alert import Alert
from app.mqtt.client import mqtt_manager

logger = logging.getLogger(__name__)

@app.task
def watchdog_orphaned_schedules():
    """
    Automated safety audit. Finds tasks stuck in 'running' state
    beyond their planned duration and kills them.
    """
    db = SessionLocal()
    redis = next(get_redis())
    now = datetime.now(timezone.utc)
    
    try:
        # Find schedules that should have ended 10 mins ago
        # Note: In a production set, we'd join with durations, 
        # but here we scan for stale running tasks (> 130 mins as global max)
        stale_limit = now - timedelta(hours=3) # Extreme safety margin
        
        orphaned = db.query(IrrigationSchedule).filter(
            IrrigationSchedule.status == "running",
            IrrigationSchedule.scheduled_at < stale_limit
        ).all()
        
        for schedule in orphaned:
            zone_id = str(schedule.zone_id)
            logger.warning(f"Watchdog found orphaned schedule {schedule.id} for Zone {zone_id}")
            
            # Kill Pump (QoS=1)
            topic_off = f"krishisarth/zone/{zone_id}/pump/off"
            mqtt_manager.publish(topic_off, "OFF", qos=1)
            
            # Update Record
            schedule.status = "failed"
            db.commit()
            
            # Release Lock
            redis.delete(f"irrigation_lock:{zone_id}")
            
            # Generate Security Alert
            alert = Alert(
                zone_id=schedule.zone_id,
                severity="warning",
                alert_type="watchdog_intervention",
                message="Safety watchdog forcibly stopped a stalled irrigation session.",
                is_read=False
            )
            db.add(alert)
            db.commit()
            
    finally:
        db.close()
