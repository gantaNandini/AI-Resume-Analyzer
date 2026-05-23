"""
Redis cache for embeddings.
Requirements: 8.4, 14.1, 14.2
"""
from __future__ import annotations
import hashlib
import json
import logging
import os
from typing import Optional

import redis as redis_lib
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("nlp_pipeline")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DEFAULT_TTL = 3600  # 1 hour

_client: Optional[redis_lib.Redis] = None  # type: ignore[type-arg]


def _get_client() -> redis_lib.Redis:  # type: ignore[type-arg]
    global _client
    if _client is None:
        _client = redis_lib.from_url(REDIS_URL, decode_responses=True)
    return _client


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def get_cached_embedding(key: str) -> Optional[dict]:
    try:
        raw = _get_client().get(f"emb:{key}")
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning("Redis get failed", extra={"error": str(e)})
    return None


def set_cached_embedding(key: str, data: dict, ttl: int = DEFAULT_TTL) -> None:
    try:
        _get_client().set(f"emb:{key}", json.dumps(data), ex=ttl)
    except Exception as e:
        logger.warning("Redis set failed", extra={"error": str(e)})


def ping() -> bool:
    try:
        return _get_client().ping()
    except Exception:
        return False
