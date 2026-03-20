from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Initialize Celery app
app = Celery(
    "krishisarth",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.irrigation_worker",
        "app.workers.watchdog_worker",
        "app.workers.alert_worker"
    ]
)

# App-level Configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    
    # Celery Beat Schedule
    beat_schedule={
        "run-ai-cycle-every-15-mins": {
            "task": "app.workers.ai_worker.run_ai_cycle",
            "schedule": crontab(minute="*/15"),
        },
        "watchdog-orphaned-schedules-every-5-mins": {
            "task": "app.workers.watchdog_worker.watchdog_orphaned_schedules",
            "schedule": crontab(minute="*/5"),
        },
    }
)

if __name__ == "__main__":
    app.start()
