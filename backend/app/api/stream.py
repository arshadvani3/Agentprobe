import json
import logging
import secrets

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ..core.settings import settings
from ..services.evaluation_store import get_evaluation
from ..services.redis_client import DONE_MSG, get_client

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)

_PING_INTERVAL_TICKS = 15  # ticks × 1s timeout = 15s between pings


@router.websocket("/stream/{eval_id}")
async def stream_evaluation(
    websocket: WebSocket,
    eval_id: str,
    token: str = Query(default=""),
) -> None:
    """
    WebSocket endpoint that streams real-time agent events for an evaluation.

    - If AGENTPROBE_API_KEY is set, a matching `token` query param is required.
    - If eval is already complete: replays stored events from Postgres then closes.
    - If eval is in-progress: subscribes to Redis pub/sub channel and forwards
      events in real-time until the DONE signal is received.
    """
    await websocket.accept()

    # Auth — only enforced when AGENTPROBE_API_KEY is configured
    if settings.agentprobe_api_key:
        provided = token or ""
        if not provided or not secrets.compare_digest(provided, settings.agentprobe_api_key):
            await websocket.close(code=4003)
            return

    record = await get_evaluation(eval_id)
    if not record:
        await websocket.send_text(
            json.dumps({"type": "error", "data": {"message": f"Evaluation {eval_id} not found"}})
        )
        await websocket.close(code=4004)
        return

    # Already finished — replay from Postgres and close
    if record["status"] in ("complete", "error"):
        for event in record.get("events", []):
            await websocket.send_text(json.dumps(event, default=str))
        await websocket.send_text(
            json.dumps({"type": "complete", "eval_id": eval_id, "data": {}})
        )
        await websocket.close()
        return

    # In-progress — subscribe to Redis pub/sub
    logger.info("WebSocket client connected for eval %s", eval_id)
    pubsub = get_client().pubsub()
    await pubsub.subscribe(f"agentprobe:eval:{eval_id}")

    tick = 0
    try:
        while True:
            # Non-blocking poll with 1-second timeout — allows keepalive pings
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )

            if message and message["type"] == "message":
                data: str = message["data"]
                if data == DONE_MSG:
                    await websocket.send_text(
                        json.dumps({"type": "complete", "eval_id": eval_id, "data": {}})
                    )
                    break
                await websocket.send_text(data)  # already JSON string from publisher
                tick = 0  # reset ping counter on real activity
            else:
                # No message this tick — send periodic keepalive
                tick += 1
                if tick >= _PING_INTERVAL_TICKS:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                    tick = 0

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from eval %s", eval_id)
    except Exception as e:
        logger.warning("WebSocket error for eval %s: %s", eval_id, e)
    finally:
        await pubsub.unsubscribe(f"agentprobe:eval:{eval_id}")
        await pubsub.aclose()
        try:
            await websocket.close()
        except Exception:
            pass
