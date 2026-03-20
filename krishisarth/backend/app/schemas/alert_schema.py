from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class AlertOut(BaseModel):
    """Detailed schema for a system alert."""
    id: UUID
    farm_id: UUID
    zone_id: Optional[UUID] = None
    severity: str  # critical | warning | info
    type: str      # SENSOR_FAULT | PUMP_FAILURE | LEAK_DETECTED | etc.
    message: str
    is_read: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AlertListResponse(BaseModel):
    """Schema for a farm-wide list of alerts with unread count."""
    alerts: List[AlertOut]
    unread_count: int
