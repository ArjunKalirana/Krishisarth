from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.postgres import get_db
from app.db.redis import get_redis
from app.models import Farmer, Farm, Zone
from app.services import auth_service

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

def get_current_farmer(
    db: Session = Depends(get_db),
    redis = Depends(get_redis),
    token: str = Depends(reusable_oauth2)
) -> Farmer:
    """
    Dependency to get the currently authenticated farmer.
    Verifies JWT signature, expiration, and JTI revocation status.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        farmer_id = payload.get("farmer_id")
        jti = payload.get("jti")
        if farmer_id is None or jti is None or payload.get("sub") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="COULD_NOT_VALIDATE_CREDENTIALS",
            )
        
        # Check JTI revocation status in Redis
        if redis.get(f"jti:{jti}:revoked"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TOKEN_REVOKED",
            )
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="COULD_NOT_VALIDATE_CREDENTIALS",
        )
        
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="FARMER_NOT_FOUND")
    return farmer

def verify_farm_owner(
    farm_id: str,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
) -> Farm:
    """Verify that the current farmer owns the requested farm."""
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == current_farmer.id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NOT_FARM_OWNER"
        )
    return farm

def verify_zone_owner(
    zone_id: str,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
) -> Zone:
    """Verify that the current farmer owns the zone via farm ownership."""
    zone = db.query(Zone).join(Farm).filter(
        Zone.id == zone_id, 
        Farm.farmer_id == current_farmer.id
    ).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="NOT_ZONE_OWNER"
        )
    return zone
