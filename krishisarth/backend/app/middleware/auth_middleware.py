from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, ExpiredSignatureError, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.postgres import get_db
from app.models import Farmer

# Use HTTPBearer for Swagger UI support
security = HTTPBearer()

def get_current_farmer(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Farmer:
    """
    Dependency to get the currently authenticated farmer.
    Extracts Bearer token, validates signature/expiry, and sets request.state.farmer.
    
    Raises:
        HTTPException(401): If token is missing, expired, or invalid.
    """
    token = credentials.credentials
    try:
        # Decode using the project's JWT secret
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        farmer_id = payload.get("farmer_id")
        
        if not farmer_id or payload.get("sub") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TOKEN_INVALID",
            )
            
        farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
        if not farmer:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="FARMER_NOT_FOUND",
            )
            
        # Store for use in other middlewares/handlers
        request.state.farmer = farmer
        return farmer
        
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOKEN_EXPIRED",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOKEN_INVALID",
        )
