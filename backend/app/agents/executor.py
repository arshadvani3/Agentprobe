import asyncio
import logging
import uuid
from datetime import datetime, timezone

from ..tools.target_caller import call_target
from ..tools.consistency_checks import run_multi_turn_conversation
from .state import EvalState

logger = logging.getLogger(__name__)

CONCURRENCY_LIMIT = 1  # Local Ollama can only handle one request at a time efficiently


def _make_event(eval_id: str, event_type: str, data: dict) -> dict:
    return {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "eval_id": eval_id,
        "agent": "executor",
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _execute_single(
    test: dict,
    target_url: str,
    target_type: str,
    model: str,
    timeout: float,
    semaphore: asyncio.Semaphore,
    progress_counter: list[int],
    total: int,
    eval_id: str,
    api_key: str = "",
) -> dict:
    async with semaphore:
        test_id = test.get("id", uuid.uuid4().hex[:6])
        category = test.get("category", "unknown")

        # Handle multi-turn conversation tests differently
        if test.get("type") == "conversation_script":
            conversation = test.get("conversation", [])
            result = await run_multi_turn_conversation(
                target_url=target_url,
                target_type=target_type,
                conversation_script=conversation,
                model=model,
                timeout=timeout,
            )
            response_text = result.get("final_response", "")
            latency_ms = 0.0
            error = "; ".join(result.get("errors", []))
        else:
            message = test.get("input", "")
            result = await call_target(
                target_url=target_url,
                target_type=target_type,
                message=message,
                model=model,
                timeout=timeout,
                api_key=api_key,
            )
            response_text = result.get("response_text", "")
            latency_ms = result.get("latency_ms", 0.0)
            error = result.get("error", "")

        progress_counter[0] += 1
        completed = progress_counter[0]
        if completed % 5 == 0 or completed == total:
            logger.info("Executor progress: %d/%d", completed, total)

        return {
            "test_id": test_id,
            "input": test.get("input", ""),
            "category": category,
            "subcategory": test.get("subcategory", ""),
            "response_text": response_text,
            "latency_ms": latency_ms,
            "error": error,
            "test_case": test,
            "skipped": bool(error),
        }


async def executor_node(state: EvalState) -> dict:
    config = state.get("config", {})
    eval_id = config.get("eval_id", "eval_000")
    target_url = config.get("target_url", "")
    target_type = config.get("target_type", "ollama")
    model = config.get("model", "")
    timeout = float(config.get("timeout", 30.0))
    api_key = config.get("api_key", "")

    # Collect ALL tests
    test_cases = state.get("test_cases", [])
    security_tests = state.get("security_tests", [])
    consistency_tests = state.get("consistency_tests", [])

    all_tests = test_cases + security_tests + consistency_tests
    total = len(all_tests)
    logger.info("Executor: running %d tests against %s", total, target_url)

    if not target_url:
        logger.error("No target URL configured")
        event = _make_event(eval_id, "error", {"message": "No target URL configured"})
        return {"execution_results": [], "agent_messages": [event], "status": "error"}

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    progress_counter = [0]

    tasks = [
        _execute_single(test, target_url, target_type, model, timeout, semaphore, progress_counter, total, eval_id, api_key)
        for test in all_tests
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    execution_results = []
    errors = 0
    for r in results:
        if isinstance(r, Exception):
            logger.warning("Test execution raised exception: %s", r)
            errors += 1
        else:
            execution_results.append(r)

    event = _make_event(eval_id, "test_executed", {
        "total": total,
        "executed": len(execution_results),
        "errors": errors,
    })
    logger.info("Executor complete: %d/%d executed, %d errors", len(execution_results), total, errors)

    return {
        "execution_results": execution_results,
        "status": "evaluating",
        "agent_messages": [event],
    }
