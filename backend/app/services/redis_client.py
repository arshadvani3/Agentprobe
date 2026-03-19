"""
Redis client — pub/sub for real-time WebSocket event streaming.
Each evaluation gets its own channel: agentprobe:eval:{eval_id}

Publish events as JSON strings; send DONE_MSG as the terminal signal.
"""
import json
import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Sentinel string published to a channel when the eval is done
DONE_MSG = "__agentprobe_done__"

_client: aioredis.Redis | None = None


async def init_redis(redis_url: str) -> None:
    global _client
    _client = aioredis.from_url(redis_url, decode_responses=True)
    await _client.ping()
    logger.info("Redis connected at %s", redis_url)


async def close_redis() -> None:
    global _client
    if _client:
        await _client.aclose()
        _client = None
        logger.info("Redis connection closed")


def get_client() -> aioredis.Redis:
    if not _client:
        raise RuntimeError("Redis not initialised — call init_redis() first")
    return _client


async def publish_event(eval_id: str, event: dict) -> None:
    """Publish a single agent event to the eval's Redis channel."""
    if not _client:
        return
    try:
        await _client.publish(
            f"agentprobe:eval:{eval_id}",
            json.dumps(event, default=str),
        )
    except Exception as e:
        logger.warning("Redis publish failed for eval %s: %s", eval_id, e)


async def publish_done(eval_id: str) -> None:
    """Signal the WebSocket consumer that the eval stream is finished."""
    if not _client:
        return
    try:
        await _client.publish(f"agentprobe:eval:{eval_id}", DONE_MSG)
    except Exception as e:
        logger.warning("Redis publish_done failed for eval %s: %s", eval_id, e)
