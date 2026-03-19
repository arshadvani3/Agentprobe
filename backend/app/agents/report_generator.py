import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..services.llm import invoke_llm
from ..tools.scoring import aggregate_scores
from .state import EvalState

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent / "prompts" / "report.txt"


def _load_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text()
    except FileNotFoundError:
        return "Write a concise reliability report based on the evaluation data."


def _make_event(eval_id: str, event_type: str, data: dict) -> dict:
    return {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "eval_id": eval_id,
        "agent": "report_generator",
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _get_top_failures(evaluations: list[dict], n: int = 10) -> list[dict]:
    """Get the n worst failures by overall score."""
    failed = [e for e in evaluations if not e.get("passed", True)]
    failed.sort(key=lambda e: e.get("scores", {}).get("overall", 1.0))
    return failed[:n]


def _get_security_findings(evaluations: list[dict]) -> list[str]:
    """Summarize security-related failures."""
    security_evals = [e for e in evaluations if e.get("category") == "prompt_injection"]
    if not security_evals:
        return []

    findings = []
    total = len(security_evals)
    succeeded = sum(1 for e in security_evals if e.get("injection_succeeded", False))

    if succeeded > 0:
        findings.append(f"Prompt injection successful: {succeeded}/{total} patterns")

    # Check by attack type
    by_type: dict[str, list] = {}
    for e in security_evals:
        t = e.get("subcategory", "unknown")
        by_type.setdefault(t, []).append(e)

    for attack_type, evals in by_type.items():
        succeeded_type = sum(1 for e in evals if e.get("injection_succeeded", False))
        if succeeded_type > 0:
            findings.append(f"{attack_type.replace('_', ' ').title()}: {succeeded_type}/{len(evals)} succeeded")

    return findings


async def report_generator_node(state: EvalState) -> dict:
    config = state.get("config", {})
    eval_id = config.get("eval_id", "eval_000")
    evaluations = state.get("evaluations", [])
    target_url = config.get("target_url", "unknown")

    # Compute aggregate stats
    agg = aggregate_scores(evaluations)
    top_failures = _get_top_failures(evaluations)
    security_findings = _get_security_findings(evaluations)

    # Build summary data for LLM
    summary_data = {
        "target_url": target_url,
        "overall_score": agg["overall"],
        "total_tests": agg["total"],
        "passed": agg["passed"],
        "failed": agg["failed"],
        "pass_rate": round(agg["passed"] / agg["total"], 3) if agg["total"] > 0 else 0,
        "category_breakdown": agg["categories"],
        "dimension_scores": agg["dimensions"],
        "security_findings": security_findings,
        "top_failures": [
            {
                "category": f.get("category"),
                "input": f.get("input", "")[:100],
                "response_preview": f.get("response", "")[:100],
                "scores": f.get("scores"),
                "failure_reason": f.get("failure_reason"),
            }
            for f in top_failures[:5]
        ],
    }

    # Generate LLM recommendations
    system = _load_prompt()
    user_message = (
        f"Evaluation data:\n{json.dumps(summary_data, indent=2)}\n\n"
        f"Write a comprehensive reliability report with executive summary, key findings, and recommendations."
    )
    try:
        narrative = await invoke_llm(system, user_message, temperature=0.3)
    except Exception as e:
        logger.warning("Report LLM failed: %s", e)
        narrative = "Report generation failed — see raw data below."

    report = {
        "eval_id": eval_id,
        "target_url": target_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "overall_score": agg["overall"],
            "total_tests": agg["total"],
            "passed": agg["passed"],
            "failed": agg["failed"],
            "pass_rate": round(agg["passed"] / agg["total"], 3) if agg["total"] > 0 else 0,
            "score_breakdown": agg["dimensions"],
        },
        "category_breakdown": agg["categories"],
        "dimension_scores": agg["dimensions"],
        "security_findings": security_findings,
        "top_failures": top_failures,
        "narrative": narrative,
    }

    event = _make_event(eval_id, "report_ready", {"eval_id": eval_id, "overall_score": agg["overall"]})
    logger.info("Report generated: overall=%.2f, %d/%d passed", agg["overall"], agg["passed"], agg["total"])

    return {
        "report": report,
        "status": "complete",
        "agent_messages": [event],
    }
