"""
Cache service.
Handles Redis connection and caching operations.
Stores frequently used data in RAM for fast access.
"""

import redis
import json
import logging
from config import REDIS_HOST, REDIS_PORT, REDIS_TTL

logger = logging.getLogger(__name__)


# Connect to Redis server
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


def set_cache(key: str, value: dict, ttl: int = REDIS_TTL) -> None:
    """
    Store data in Redis cache.

    Args:
        key: unique name for this cached item
             example: "stock_price:AAPL"
        value: data to store (dictionary)
        ttl: how long to keep it (seconds)
             default: 300 seconds = 5 minutes
    """
    try:
        redis_client.setex(key, ttl, json.dumps(value))
        logger.info(f"Cached: {key} for {ttl} seconds")
    except Exception as e:
        logger.error(f"Cache set failed for {key}: {e}")


def get_cache(key: str) -> dict | None:
    """
    Retrieve data from Redis cache.

    Args:
        key: unique name of cached item
             example: "stock_price:AAPL"

    Returns:
        cached data if found
        None if not found or expired
    """
    try:
        data = redis_client.get(key)
        if data:
            logger.info(f"Cache HIT: {key}")
            return json.loads(data)
        logger.info(f"Cache MISS: {key}")
        return None
    except Exception as e:
        logger.error(f"Cache get failed for {key}: {e}")
        return None


def delete_cache(key: str) -> None:
    """
    Manually delete a cached item.
    Used when data changes and cache must be refreshed.

    Args:
        key: unique name of cached item to delete
    """
    try:
        redis_client.delete(key)
        logger.info(f"Cache deleted: {key}")
    except Exception as e:
        logger.error(f"Cache delete failed for {key}: {e}")


def clear_all_cache() -> None:
    """
    Clear ALL cached data.
    Use carefully — removes everything from Redis.
    """
    try:
        redis_client.flushdb()
        logger.info("All cache cleared")
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")


def is_cached(key: str) -> bool:
    """
    Check if a key exists in cache.

    Args:
        key: unique name of cached item

    Returns:
        True if cached, False if not
    """
    try:
        return redis_client.exists(key) > 0
    except Exception as e:
        logger.error(f"Cache check failed for {key}: {e}")
        return False


def get_cache_ttl(key: str) -> int:
    """
    Get how many seconds until a cached item expires.

    Args:
        key: unique name of cached item

    Returns:
        seconds remaining
        -1 if key exists but has no expiry
        -2 if key does not exist
    """
    try:
        return redis_client.ttl(key)
    except Exception as e:
        logger.error(f"Cache TTL check failed for {key}: {e}")
        return -2