import time
from fastapi import Request, HTTPException, status, Depends
from app.db.redis import get_redis

def rate_limit(request: Request, redis = Depends(get_redis)):
    """
    Sliding window rate limit (per minute) using Redis.
    Key: rl:{token_fragment}:{minute_timestamp}
    
    Limit: 100 requests per minute.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return  # Pass-through for unauthenticated paths (e.g., login/health)
        
    token = auth_header.split(" ")[1]
    # Use first 16 chars as a reasonably unique but non-identifiable key fragment
    token_fragment = token[:16]
    minute_ts = int(time.time() // 60)
    key = f"rl:{token_fragment}:{minute_ts}"
    
    try:
        count = redis.incr(key)
        if count == 1:
            redis.expire(key, 60)
            
        if count > 100:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="RATE_LIMIT_EXCEEDED",
                headers={"Retry-After": "60"}
            )
    except Exception:
        # Fallback: if Redis is down, allow request to proceed (Fail-Open for availability)
        pass
