from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

class IrrigateRequest(BaseModel):
    """Schema for manual irrigation request."""
    duration_min: int = Field(10, ge=1, le=120)
    source: str = "manual"

class FertigationRequest(BaseModel):
    """Schema for nutrient injection request."""
    nutrient_type: str = Field(..., min_length=1)
    concentration_ml: float = Field(0, ge=0, le=30)

class IrrigateResponse(BaseModel):
    """Data returned starting a successful irrigation."""
    schedule_id: UUID
    zone_id: UUID
    duration_min: int
    status: str
    started_at: datetime
    estimated_end_at: datetime

class StopResponse(BaseModel):
    """Data returned after manually stopping a pump."""
    zone_id: UUID
    pump_stopped: bool
    water_used_l: float
    stopped_at: datetime
