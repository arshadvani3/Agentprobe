import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..services.llm import invoke_llm
from ..tools.consistency_checks import generate_paraphrases
from .state import EvalState

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent / "prompts" / "consistency.txt"

_MAX_BASE_QUESTIONS = 5
_PARAPHRASES_PER_QUESTION = 3


def _load_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text()
    except FileNotFoundError:
        return "Generate consistency tests as a JSON array."


def _make_event(eval_id: str, event_type: str, data: dict) -> dict:
    return {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "eval_id": eval_id,
        "agent": "consistency_agent",
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def consistency_agent_node(state: EvalState) -> dict:
    config = state.get("config", {})
    test_cases = state.get("test_cases", [])
    eval_id = config.get("eval_id", "eval_000")
    target_description = config.get("target_description", "A general-purpose AI chatbot")

    all_consistency_tests: list[dict] = []

    # 1. Pick up to 5 base questions from existing test cases (happy path / edge cases)
    base_questions = [
        tc for tc in test_cases
        if tc.get("category") in ("happy_path", "edge_cases")
        and isinstance(tc.get("input"), str)
    ][:_MAX_BASE_QUESTIONS]

    # 2. Generate paraphrase groups
    for tc in base_questions:
        base_q = tc["input"]
        try:
            paraphrases = await generate_paraphrases(base_q, count=_PARAPHRASES_PER_QUESTION)
            all_consistency_tests.append({
                "id": f"con_para_{uuid.uuid4().hex[:6]}",
                "category": "consistency",
                "subcategory": "paraphrase",
                "type": "paraphrase_group",
                "base_question": base_q,
                "variants": paraphrases,
                "input": base_q,
                "expected_behavior": "All variants should produce semantically equivalent answers",
                "difficulty": "medium",
                "metadata": {"source_test_id": tc.get("id")},
            })
        except Exception as e:
            logger.warning("Failed to generate paraphrases for '%s': %s", base_q[:50], e)

    # 3. Generate multi-turn conversation scripts via LLM
    system = _load_prompt()
    user_message = (
        f"Agent description: {target_description}\n\n"
        f"Generate 3 multi-turn conversation scripts that test context retention and contradiction handling. "
        f"Each conversation should have 3-5 turns. Output a JSON array."
    )
    try:
        raw = await invoke_llm(system, user_message, temperature=0.7)
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            llm_tests = json.loads(raw[start : end + 1])
            for t in llm_tests:
                if not t.get("id"):
                    t["id"] = f"con_llm_{uuid.uuid4().hex[:6]}"
                t.setdefault("category", "consistency")
                t.setdefault("input", str(t.get("conversation", [{}])[0].get("content", "")))
            all_consistency_tests.extend(llm_tests)
            logger.info("LLM generated %d consistency tests", len(llm_tests))
    except Exception as e:
        logger.warning("LLM consistency test generation failed: %s", e)

    event = _make_event(eval_id, "consistency_result", {"consistency_test_count": len(all_consistency_tests)})
    logger.info("Consistency agent produced %d tests", len(all_consistency_tests))

    return {
        "consistency_tests": all_consistency_tests,
        "agent_messages": [event],
    }
