"""Minimal async Redis cache + monthly call-counter helpers.

Used by providers/APIs with tight usage quotas (e.g. RentCast's free tier:
50 requests/month) to avoid burning quota on repeat calls and to hard-stop
before exceeding the quota rather than just hoping caching is enough.
"""

import json
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(get_settings().redis_url, decode_responses=True)
    return _redis_client


async def cache_get_json(key: str) -> Any | None:
    raw = await _get_client().get(key)
    return json.loads(raw) if raw is not None else None


async def cache_set_json(key: str, value: Any, ttl_seconds: int) -> None:
    await _get_client().set(key, json.dumps(value), ex=ttl_seconds)


async def increment_monthly_counter(namespace: str, limit: int) -> int:
    """Atomically increment this month's call counter for `namespace` and
    return the new count. Callers should check the result against `limit`
    themselves *before* making the call the counter represents, since this
    only tracks usage — it doesn't block anything on its own.
    """
    month_key = f"quota:{namespace}:{datetime.now(UTC):%Y-%m}"
    client = _get_client()
    count = await client.incr(month_key)
    if count == 1:
        # First increment this month: expire ~32 days out so the key
        # self-cleans without needing a scheduled job.
        await client.expire(month_key, 32 * 24 * 3600)
    if count > limit:
        logger.warning("quota.exceeded", namespace=namespace, count=count, limit=limit)
    return count
