from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.models import Farm, Zone

def verify_farm_owner(
    farm_id: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Farm:
    """
    Verify that the current farmer owns the requested farm.
    
    Rules:
    - If farm doesn't exist -> 404
    - If farm exists but belongs to another -> 403 (Security Rule)
    
    Returns:
        The Farm object if verification succeeds.
    """
    farmer = getattr(request.state, "farmer", None)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="FARM_NOT_FOUND"
        )
        
    if str(farm.farmer_id) != str(farmer.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="NOT_FARM_OWNER"
        )
        
    return farm

def verify_zone_owner(
    zone_id: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Zone:
    """
    Verify that the current farmer owns the requested zone via farm ownership.
    
    Returns:
        The Zone object if verification succeeds.
    """
    farmer = getattr(request.state, "farmer", None)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="ZONE_NOT_FOUND"
        )
        
    # Verify farm ownership linked to this zone
    farm = db.query(Farm).filter(Farm.id == zone.farm_id).first()
    if not farm or str(farm.farmer_id) != str(farmer.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="NOT_ZONE_OWNER"
        )
        
    return zone
