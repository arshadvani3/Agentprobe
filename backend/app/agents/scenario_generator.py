import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ..services.llm import invoke_llm
from ..services.chroma_store import add_tests as chroma_add, is_duplicate, seed_from_tests
from ..tools.test_generators import (
    generate_happy_path_tests,
    generate_edge_case_tests,
    generate_adversarial_tests,
    generate_hallucination_traps,
    generate_out_of_scope_tests,
)
from .state import EvalState

logger = logging.getLogger(__name__)

_SUITES_DIR = Path(__file__).parent.parent.parent / "test_suites"


def _load_suite(suite_name: str) -> list[dict]:
    """Load test cases from a YAML test suite file."""
    path = _SUITES_DIR / f"{suite_name}.yaml"
    if not path.exists():
        logger.warning("Test suite not found: %s", path)
        return []
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return data.get("tests", [])
    except Exception as e:
        logger.warning("Failed to load suite %s: %s", suite_name, e)
        return []


def _make_event(eval_id: str, event_type: str, data: dict) -> dict:
    return {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "eval_id": eval_id,
        "agent": "scenario_generator",
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _parse_plan(test_plan: list[str]) -> dict[str, int]:
    """Parse 'category:count' strings from the test plan."""
    result = {}
    for item in test_plan:
        if ":" in item:
            cat, _, count_str = item.partition(":")
            try:
                result[cat.strip()] = int(count_str.strip())
            except ValueError:
                result[cat.strip()] = 3
        else:
            result[item.strip()] = 3
    return result


async def scenario_generator_node(state: EvalState) -> dict:
    config = state.get("config", {})
    test_plan = state.get("test_plan", [])
    eval_id = config.get("eval_id", "eval_000")
    suite_name = config.get("suite", "general_chatbot")
    target_description = config.get("target_description", "A general-purpose AI chatbot assistant")

    category_counts = _parse_plan(test_plan)
    all_tests: list[dict] = []

    # Load pre-built test suite and seed ChromaDB so generated tests can deduplicate against them
    suite_tests = _load_suite(suite_name)
    logger.info("Loaded %d tests from suite '%s'", len(suite_tests), suite_name)
    seed_from_tests(suite_tests, suite_name=suite_name)
    all_tests.extend(suite_tests)

    # Generate additional tests via LLM for each category
    generator_map = {
        "happy_path": lambda count: generate_happy_path_tests(target_description, count),
        "edge_cases": lambda count: generate_edge_case_tests(target_description, count),
        "adversarial": lambda count: generate_adversarial_tests(target_description, count),
        "hallucination_traps": lambda count: generate_hallucination_traps(count),
        "out_of_scope": lambda count: generate_out_of_scope_tests(target_description, count),
    }

    for category, count in category_counts.items():
        if category in ("prompt_injection", "consistency"):
            # These are handled by specialized agents
            continue
        generator = generator_map.get(category)
        if generator:
            try:
                tests = await generator(count)
                # Filter out tests semantically similar to ones already in the store
                novel_tests = [t for t in tests if not is_duplicate(t.get("input", ""))]
                skipped = len(tests) - len(novel_tests)
                if skipped:
                    logger.info("ChromaDB deduplicated %d/%d %s tests", skipped, len(tests), category)
                chroma_add(novel_tests, eval_id=eval_id, category=category)
                logger.info("Generated %d %s tests (%d novel)", len(tests), category, len(novel_tests))
                all_tests.extend(novel_tests)
            except Exception as e:
                logger.warning("Failed to generate %s tests: %s", category, e)

    # Deduplicate by id
    seen_ids: set[str] = set()
    unique_tests = []
    for t in all_tests:
        tid = t.get("id", uuid.uuid4().hex[:6])
        t["id"] = tid
        if tid not in seen_ids:
            seen_ids.add(tid)
            unique_tests.append(t)

    event = _make_event(eval_id, "tests_generated", {"count": len(unique_tests), "categories": list(category_counts.keys())})
    logger.info("Scenario generator produced %d test cases", len(unique_tests))

    return {
        "test_cases": unique_tests,
        "agent_messages": [event],
    }
