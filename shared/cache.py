"""
Shared Redis cache utility used across all services.
Requirements: 14.3, 14.5
"""
from __future__ import annotations
import json
import logging
import os
from typing import Optional

import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("shared.cache")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_client: Optional[aioredis.Redis] = None  # type: ignore[type-arg]


def _get_client() -> aioredis.Redis:  # type: ignore[type-arg]
    global _client
    if _client is None:
        _client = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _client


async def get(key: str) -> Optional[str]:
    """Get a value from Redis. Returns None on miss or connection error."""
    try:
        return await _get_client().get(key)
    except Exception as e:
        logger.warning("Redis GET failed", extra={"key": key, "error": str(e)})
        return None


async def set(key: str, value: str, ttl: int = 3600) -> None:
    """Set a value in Redis with TTL. Silently fails on connection error."""
    try:
        await _get_client().set(key, value, ex=ttl)
    except Exception as e:
        logger.warning("Redis SET failed", extra={"key": key, "error": str(e)})


async def delete(key: str) -> None:
    """Delete a key from Redis."""
    try:
        await _get_client().delete(key)
    except Exception as e:
        logger.warning("Redis DELETE failed", extra={"key": key, "error": str(e)})


async def ping() -> bool:
    """Check Redis connectivity."""
    try:
        return await _get_client().ping()
    except Exception:
        return False


def get_json(key: str) -> Optional[dict]:
    """Synchronous JSON get using sync redis client."""
    import redis as sync_redis
    try:
        client = sync_redis.from_url(REDIS_URL, decode_responses=True)
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning("Redis sync GET failed", extra={"key": key, "error": str(e)})
        return None


def set_json(key: str, value: dict, ttl: int = 3600) -> None:
    """Synchronous JSON set using sync redis client."""
    import redis as sync_redis
    try:
        client = sync_redis.from_url(REDIS_URL, decode_responses=True)
        client.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        logger.warning("Redis sync SET failed", extra={"key": key, "error": str(e)})
