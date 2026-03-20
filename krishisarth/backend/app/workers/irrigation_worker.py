import time
import asyncio
import logging
from datetime import datetime, timezone
from app.workers.celery_app import app
from app.db.postgres import SessionLocal
from app.db.redis import get_redis
from app.models.irrigation_schedule import IrrigationSchedule
from app.models.alert import Alert
from app.mqtt.client import mqtt_manager

logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=1)
def execute_irrigation(self, schedule_id, zone_id, duration_min):
    """
    Asynchronous task to execute a physical irrigation event.
    Standard flow: ON -> Sleep -> OFF.
    Safety Rules: QoS=1 for all pump messages.
    """
    db = SessionLocal()
    redis = next(get_redis())
    
    try:
        # 1. Physical Trigger: Start Pump (QoS=1 Required)
        topic_on = f"krishisarth/zone/{zone_id}/pump/on"
        # In a real environment, we'd wait for an ACK on pump/ack topic
        mqtt_manager.publish(topic_on, "ON", qos=1)
        logger.info(f"Pump ON sent for Zone {zone_id} | QoS=1")
        
        # 2. Precision Delay: Execute based on requested duration
        time.sleep(duration_min * 60)
        
        # 3. Physical Trigger: Stop Pump (QoS=1 Required)
        topic_off = f"krishisarth/zone/{zone_id}/pump/off"
        mqtt_manager.publish(topic_off, "OFF", qos=1)
        logger.info(f"Pump OFF sent for Zone {zone_id} | QoS=1")
        
        # 4. Persistence: Update schedule as completed
        schedule = db.query(IrrigationSchedule).filter(IrrigationSchedule.id == schedule_id).first()
        if schedule:
            schedule.status = "completed"
            schedule.executed_at = datetime.now(timezone.utc)
            db.commit()
            
    except Exception as e:
        logger.error(f"Irrigation Task Failed: {str(e)}")
        # Fail-Safe state update
        schedule = db.query(IrrigationSchedule).filter(IrrigationSchedule.id == schedule_id).first()
        if schedule:
            schedule.status = "failed"
            db.commit()
            
        # Security: Create critical alert for hardware failure
        alert = Alert(
            zone_id=zone_id,
            severity="critical",
            alert_type="hardware_error",
            message=f"Irrigation task execution failure for Zone {zone_id}",
            is_read=False
        )
        db.add(alert)
        db.commit()
        raise e
        
    finally:
        # Cleanup: Release pump lock
        redis.delete(f"irrigation_lock:{zone_id}")
        db.close()
