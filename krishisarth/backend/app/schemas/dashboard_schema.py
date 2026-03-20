from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class DashboardSummary(BaseModel):
    """Aggregated farm metrics for the dashboard header."""
    water_saved_today_l: float
    system_status: str
    next_irrigation_at: Optional[datetime]
    active_zones: int
    offline_devices: int

class ZoneDashboard(BaseModel):
    """Detailed telemetry and status for a single zone."""
    id: UUID
    name: str
    moisture_pct: float
    moisture_status: str  # dry / ok / wet
    temp_c: Optional[float] = None
    ec_ds_m: Optional[float] = None
    pump_running: bool = False

class WaterQualityDashboard(BaseModel):
    """Latest water quality sensor readings."""
    ph: Optional[float] = None
    ec_ms_cm: Optional[float] = None
    turbidity_ntu: Optional[float] = None
    nitrate_ppm: Optional[float] = None

class DashboardOut(BaseModel):
    """Main dashboard data response model."""
    summary: DashboardSummary
    zones: List[ZoneDashboard]
    water_quality: WaterQualityDashboard
    tank_level_pct: float
    unread_alerts: int
    data_source: str = "live"  # live / cache

    model_config = ConfigDict(from_attributes=True)
