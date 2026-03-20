from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

class RegisterRequest(BaseModel):
    """Request model for farmer registration."""
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: Optional[str] = None
    preferred_lang: str = "en"

class LoginRequest(BaseModel):
    """Request model for farmer login."""
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str

class AuthData(BaseModel):
    """Authentication data returned on successful login/register."""
    farmer_id: UUID
    name: str
    email: str
    access_token: str
    refresh_token: str
    expires_in: int = 86400  # 24h for access token

class RefreshData(BaseModel):
    """Data returned on successful token refresh."""
    access_token: str
    refresh_token: str
    expires_in: int = 86400

class AuthResponse(BaseModel):
    """Standardized response envelope for authentication."""
    success: bool = True
    data: AuthData

class RefreshResponse(BaseModel):
    """Standardized response envelope for token refresh."""
    success: bool = True
    data: RefreshData
