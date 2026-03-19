import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..services.llm import invoke_llm
from .state import EvalState

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent / "prompts" / "supervisor.txt"

# Default test counts per depth
_DEPTH_COUNTS = {
    "quick": {"happy_path": 3, "edge_cases": 2, "adversarial": 2, "hallucination_traps": 2, "out_of_scope": 2, "prompt_injection": 5, "consistency": 2},
    "standard": {"happy_path": 5, "edge_cases": 3, "adversarial": 3, "hallucination_traps": 3, "out_of_scope": 3, "prompt_injection": 10, "consistency": 3},
    "deep": {"happy_path": 8, "edge_cases": 5, "adversarial": 5, "hallucination_traps": 5, "out_of_scope": 5, "prompt_injection": 15, "consistency": 5},
}


def _load_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text()
    except FileNotFoundError:
        return "Create a test plan as JSON."


def _make_event(eval_id: str, event_type: str, data: dict) -> dict:
    return {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "eval_id": eval_id,
        "agent": "supervisor",
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def supervisor_node(state: EvalState) -> dict:
    config = state.get("config", {})
    iteration = state.get("iteration", 0)
    evaluations = state.get("evaluations", [])
    eval_id = config.get("eval_id", "eval_000")
    depth = config.get("depth", "standard")

    # Check if this is a retry (pass rate was too high)
    is_retry = iteration > 0

    if is_retry and evaluations:
        passed = sum(1 for e in evaluations if e.get("passed", False))
        pass_rate = passed / len(evaluations) if evaluations else 0
        logger.info("Supervisor retry: pass_rate=%.2f, iteration=%d", pass_rate, iteration)

    # Build the test plan via LLM
    system = _load_prompt()
    target_type = config.get("target_type", "general_chatbot")
    categories = config.get("categories") or list(_DEPTH_COUNTS.get(depth, _DEPTH_COUNTS["standard"]).keys())

    user_message = (
        f"Target type: {target_type}\n"
        f"Depth: {depth}\n"
        f"Requested categories: {categories}\n"
        f"Iteration: {iteration} (0=first run, 1+=retry with harder tests)\n"
        + (f"Previous pass rate: {passed / len(evaluations):.0%} — make tests HARDER\n" if is_retry and evaluations else "")
        + "\nCreate a test plan as JSON."
    )

    try:
        raw = await invoke_llm(system, user_message, temperature=0.3)
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            plan_data = json.loads(raw[start : end + 1])
        else:
            raise ValueError("No JSON in supervisor response")
    except Exception as e:
        logger.warning("Supervisor LLM failed, using defaults: %s", e)
        plan_data = {
            "categories": categories,
            "counts": _DEPTH_COUNTS.get(depth, _DEPTH_COUNTS["standard"]),
            "rationale": "Default plan (LLM unavailable)",
            "depth": depth,
        }

    # If retry, increase counts by 50%
    if is_retry:
        for k in plan_data.get("counts", {}):
            plan_data["counts"][k] = int(plan_data["counts"].get(k, 3) * 1.5)

    # Build test_plan as list of strings for state
    counts = plan_data.get("counts", _DEPTH_COUNTS.get(depth, _DEPTH_COUNTS["standard"]))
    test_plan = [f"{cat}:{counts.get(cat, 3)}" for cat in plan_data.get("categories", categories)]

    event = _make_event(eval_id, "plan_created", {"test_plan": test_plan, "iteration": iteration + 1})
    logger.info("Supervisor created plan: %s", test_plan)

    return {
        "test_plan": test_plan,
        "status": "generating",
        "iteration": iteration + 1,
        "agent_messages": [event],
        "config": {**config, "plan_counts": counts},
    }
