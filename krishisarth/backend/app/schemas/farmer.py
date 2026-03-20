from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

class FarmerBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    preferred_lang: Optional[str] = "en"

class FarmerCreate(FarmerBase):
    password: str = Field(..., min_length=8)

class FarmerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    preferred_lang: Optional[str] = None

class Farmer(FarmerBase):
    id: UUID

    class Config:
        from_attributes = True
