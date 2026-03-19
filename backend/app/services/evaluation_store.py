"""
Evaluation store — public API for all evaluation CRUD + background execution.
Phase 4: backed by PostgreSQL (persistence) + Redis (real-time pub/sub).

All functions are async. Callers must await them.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from ..agents.graph import app as langgraph_app
from ..agents.state import EvalState
from ..models.schemas import EvalStatus
from . import database, redis_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public CRUD — thin wrappers over database.py
# ---------------------------------------------------------------------------

async def create_evaluation(request_data: dict) -> str:
    """Insert a new evaluation record. Returns eval_id."""
    return await database.create_evaluation(request_data)


async def get_evaluation(eval_id: str) -> dict[str, Any] | None:
    return await database.get_evaluation(eval_id)


async def list_evaluations() -> list[dict[str, Any]]:
    return await database.list_evaluations()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _emit(eval_id: str, event: dict) -> None:
    """Store event in Postgres and publish to Redis channel."""
    await database.append_event(eval_id, event)
    await redis_client.publish_event(eval_id, event)


def _make_system_event(eval_id: str, event_type: str, data: dict) -> dict:
    return {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "eval_id": eval_id,
        "agent": "system",
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Background graph runner
# ---------------------------------------------------------------------------

async def run_evaluation(eval_id: str, request_data: dict) -> None:
    """Run the LangGraph evaluation graph as a background task."""
    record = await database.get_evaluation(eval_id)
    if not record:
        return

    await database.update_status(eval_id, EvalStatus.planning)

    # Load custom tests if a custom_suite_id was provided — they are injected
    # as pre-seeded test_cases so the executor runs them alongside generated ones.
    custom_tests: list[dict] = []
    custom_suite_id = request_data.get("custom_suite_id")
    if custom_suite_id:
        row = await database.get_custom_suite(custom_suite_id)
        if row:
            custom_tests = row.get("tests") or []
            logger.info(
                "Injecting %d custom tests from suite %s into eval %s",
                len(custom_tests), custom_suite_id, eval_id,
            )
        else:
            logger.warning("Custom suite %s not found — skipping", custom_suite_id)

    initial_state: EvalState = {
        "config": {
            "eval_id": eval_id,
            "target_url": request_data["target_url"],
            "target_type": request_data["target_type"],
            "suite": request_data["suite"],
            "categories": request_data.get("categories"),
            "depth": request_data["depth"],
            "model": request_data.get("model", ""),
            "timeout": request_data.get("timeout", 30.0),
            "api_key": request_data.get("api_key", ""),
            "target_description": request_data.get(
                "target_description", "A general-purpose AI assistant"
            ),
            "custom_suite_id": custom_suite_id,
        },
        "test_plan": [],
        "test_cases": custom_tests,  # pre-seed; scenario generator appends more
        "security_tests": [],
        "consistency_tests": [],
        "execution_results": [],
        "evaluations": [],
        "report": {},
        "agent_messages": [],
        "iteration": 0,
        "status": "planning",
    }

    # Per-request timeout from config, plus generous overhead for the full graph.
    # Prevents stuck target agents from hanging the worker indefinitely.
    per_call_timeout = request_data.get("timeout", 30.0)
    total_timeout = max(3600.0, per_call_timeout * 200)  # at least 1 hr, scales with test count

    try:
        async with asyncio.timeout(total_timeout):
            async for chunk in langgraph_app.astream(initial_state, stream_mode="updates"):
                for _node, updates in chunk.items():
                    # Forward all agent_messages as WebSocket events
                    for event in updates.get("agent_messages", []):
                        await _emit(eval_id, event)

                    # Persist status changes
                    if updates.get("status"):
                        await database.update_status(eval_id, updates["status"])

                    # Persist report when ready
                    if updates.get("report"):
                        report = updates["report"]
                        summary = report.get("summary", {})
                        await database.set_report(
                            eval_id,
                            report,
                            overall_score=summary.get("overall_score", 0.0),
                            total=summary.get("total_tests", 0),
                            passed=summary.get("passed", 0),
                            failed=summary.get("failed", 0),
                        )

        await database.complete_evaluation(eval_id, EvalStatus.complete)

        done_event = _make_system_event(eval_id, "complete", {"eval_id": eval_id})
        await _emit(eval_id, done_event)

    except asyncio.TimeoutError:
        logger.error("Evaluation %s timed out after %.0fs", eval_id, total_timeout)
        await database.complete_evaluation(eval_id, EvalStatus.error)
        error_event = _make_system_event(eval_id, "error", {"message": f"Evaluation timed out after {total_timeout:.0f}s"})
        await _emit(eval_id, error_event)
    except Exception as e:
        logger.exception("Evaluation %s failed: %s", eval_id, e)
        await database.complete_evaluation(eval_id, EvalStatus.error)
        error_event = _make_system_event(eval_id, "error", {"message": str(e)})
        await _emit(eval_id, error_event)

    finally:
        await redis_client.publish_done(eval_id)
