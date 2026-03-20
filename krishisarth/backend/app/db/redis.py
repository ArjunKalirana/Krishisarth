import redis
import json
from typing import Any, Optional
from app.core.config import settings

# Singleton Redis client
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

def get_redis() -> redis.Redis:
    """Returns the singleton Redis client instance."""
    return redis_client

def ping_redis() -> bool:
    """
    Verify Redis connectivity using the PING command.
    Returns True if successful, False otherwise.
    """
    try:
        return redis_client.ping()
    except Exception:
        return False

def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """
    Store a value in Redis with an optional TTL in seconds.
    Values are automatically serialized to JSON.
    """
    serialized_value = json.dumps(value)
    redis_client.set(key, serialized_value, ex=ttl)

def cache_get(key: str) -> Optional[Any]:
    """
    Retrieve and deserialize a value from Redis.
    Returns None if the key does not exist.
    """
    value = redis_client.get(key)
    if value:
        return json.loads(value)
    return None

def cache_delete(key: str) -> None:
    """Remove a key from Redis."""
    redis_client.delete(key)
