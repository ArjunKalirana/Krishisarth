from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

class ZoneCreate(BaseModel):
    """Schema for creating a new zone."""
    name: str = Field(..., min_length=1, max_length=100)
    crop_type: Optional[str] = None
    crop_stage: Optional[str] = None
    area_sqm: Optional[float] = Field(None, gt=0)

class ZonePatch(BaseModel):
    """Schema for updating (patching) an existing zone."""
    crop_type: Optional[str] = None
    crop_stage: Optional[str] = None
    is_active: Optional[bool] = None

class ZoneOut(BaseModel):
    """Schema for zone output data."""
    id: UUID
    farm_id: UUID
    name: str
    crop_type: Optional[str]
    crop_stage: Optional[str]
    area_sqm: Optional[float]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
