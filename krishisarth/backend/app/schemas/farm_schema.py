from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

class FarmCreate(BaseModel):
    """Schema for creating a new farm."""
    name: str = Field(..., min_length=1, max_length=100)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lng: Optional[float] = Field(None, ge=-180, le=180)
    area_ha: Optional[float] = Field(None, gt=0)
    soil_type: Optional[str] = None

class FarmOut(BaseModel):
    """Schema for farm output data."""
    id: UUID
    name: str
    lat: Optional[float]
    lng: Optional[float]
    area_ha: Optional[float]
    soil_type: Optional[str]
    zone_count: int = 0
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class FarmListResponse(BaseModel):
    """Data structure for a paginated list of farms."""
    farms: List[FarmOut]
    total: int
    page: int
    limit: int
