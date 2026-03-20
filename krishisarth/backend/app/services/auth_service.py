import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import bcrypt
from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.core.config import settings

ALGORITHM = "HS256"

def hash_password(plain: str) -> str:
    """
    Hash a password using bcrypt with cost factor 12.
    
    Args:
        plain: The plain text password to hash.
        
    Returns:
        The hashed password string.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain password against a bcrypt hash.
    
    Args:
        plain: The plain text password.
        hashed: The hashed password.
        
    Returns:
        True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(farmer_id: str) -> str:
    """
    Generate an access token for a farmer.
    
    Payload structure:
    {
        "sub": "access",
        "farmer_id": str(farmer_id),
        "jti": str(uuid.uuid4()),
        "exp": now + 24h,
        "iat": now
    }
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=24)
    to_encode = {
        "sub": "access",
        "farmer_id": str(farmer_id),
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": now
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)

def create_refresh_token(farmer_id: str) -> Tuple[str, str]:
    """
    Generate a refresh token and return its string representation and JTI.
    
    Payload structure:
    {
        "sub": "refresh",
        "farmer_id": str(farmer_id),
        "jti": uuid4(),
        "exp": now + 30d,
        "iat": now
    }
    
    Args:
        farmer_id: The UUID of the farmer.
        
    Returns:
        A tuple of (token_string, jti).
    """
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=30)
    to_encode = {
        "sub": "refresh",
        "farmer_id": str(farmer_id),
        "jti": jti,
        "exp": expire,
        "iat": now
    }
    token = jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm=ALGORITHM)
    return token, jti

async def rotate_refresh_token(old_token: str, redis) -> Tuple[str, str, str]:
    """
    Verify an old refresh token, revoke its JTI, and issue a new token pair.
    
    Args:
        old_token: The refresh token to be rotated.
        redis: Redis client for JTI revocation check.
        
    Returns:
        A tuple of (new_access_token, new_refresh_token, farmer_id).
        
    Raises:
        HTTPException(401): If the token is invalid, expired, or reused.
    """
    try:
        payload = jwt.decode(
            old_token, 
            settings.JWT_REFRESH_SECRET, 
            algorithms=[ALGORITHM]
        )
        if payload.get("sub") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="INVALID_TOKEN_TYPE"
            )
        
        farmer_id = payload.get("farmer_id")
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if not farmer_id or not jti or not exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="INVALID_TOKEN_PAYLOAD"
            )

        # Check for reuse/revocation
        if redis.get(f"revoked_jti:{jti}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="TOKEN_REUSED"
            )
        
        # Revoke old JTI (Replay prevention)
        now = datetime.now(timezone.utc).timestamp()
        ttl = int(exp - now) if exp > now else 1
        redis.setex(f"revoked_jti:{jti}", ttl, "1")
        
        # Issue new pair
        new_access = create_access_token(farmer_id)
        new_refresh, _ = create_refresh_token(farmer_id)
        
        return new_access, new_refresh, farmer_id

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="COULD_NOT_VALIDATE_CREDENTIALS"
        )

async def check_brute_force(email: str, redis) -> None:
    """
    Check if a login lockout is active for the given email.
    
    Args:
        email: The farmer's email.
        redis: Redis client.
        
    Raises:
        HTTPException(429): If the account is locked.
    """
    if redis.get(f"login_lock:{email}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="ACCOUNT_LOCKED"
        )

async def record_login_failure(email: str, redis) -> None:
    """
    Track failed login attempts and impose lockout after 5 failures.
    
    Args:
        email: The farmer's email.
        redis: Redis client.
    """
    fail_key = f"login_fail:{email}"
    lock_key = f"login_lock:{email}"
    
    attempts = redis.incr(fail_key)
    if attempts == 1:
        redis.expire(fail_key, 600)  # 10 minute window
    
    if attempts >= 5:
        redis.setex(lock_key, 900, "1")  # 15 minute lockout

async def clear_login_failures(email: str, redis) -> None:
    """
    Clear failed login attempts on successful login.
    
    Args:
        email: The farmer's email.
        redis: Redis client.
    """
    redis.delete(f"login_fail:{email}")
