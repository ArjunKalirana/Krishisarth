from app.db.postgres import Base
from app.models.farmer import Farmer
from app.models.farm import Farm
from app.models.zone import Zone
from app.models.device import Device
from app.models.irrigation_schedule import IrrigationSchedule
from app.models.ai_decision import AIDecision
from app.models.fertigation_log import FertigationLog
from app.models.alert import Alert

# This allows Alembic to discover models via one import
__all__ = [
    "Base",
    "Farmer",
    "Farm",
    "Zone",
    "Device",
    "IrrigationSchedule",
    "AIDecision",
    "FertigationLog",
    "Alert",
]
