import json
import logging
from typing import Any

from ..services.llm import invoke_llm
from .target_caller import call_target

logger = logging.getLogger(__name__)


async def generate_paraphrases(question: str, count: int = 3) -> list[str]:
    """Generate paraphrased versions of a question using the LLM."""
    system = "You are a linguistic expert. Generate rephrased versions of questions that mean the same thing but use different words and structure."
    prompt = (
        f"Generate {count} different ways to ask this question, each using different wording:\n"
        f"Original: {question}\n\n"
        f"Output ONLY a JSON array of strings, no explanation:\n"
        f'["paraphrase 1", "paraphrase 2", ...]'
    )
    raw = await invoke_llm(system, prompt, temperature=0.8)
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1:
        return [question]
    try:
        paraphrases = json.loads(raw[start : end + 1])
        return [p for p in paraphrases if isinstance(p, str)]
    except json.JSONDecodeError:
        return [question]


def compare_responses(responses: list[str]) -> dict[str, Any]:
    """
    Simple lexical/heuristic similarity check between responses.
    Returns a consistency score (0-1) and a flag if responses differ significantly.
    """
    if len(responses) < 2:
        return {"consistent": True, "score": 1.0, "reason": "Only one response to compare"}

    # Check if all responses are present
    non_empty = [r for r in responses if r and r.strip()]
    if not non_empty:
        return {"consistent": False, "score": 0.0, "reason": "All responses are empty"}

    # Simple word overlap similarity
    def word_set(text: str) -> set[str]:
        return set(text.lower().split())

    scores = []
    first_words = word_set(non_empty[0])
    for resp in non_empty[1:]:
        other_words = word_set(resp)
        if not first_words and not other_words:
            scores.append(1.0)
        elif not first_words or not other_words:
            scores.append(0.0)
        else:
            intersection = len(first_words & other_words)
            union = len(first_words | other_words)
            scores.append(intersection / union)

    avg_score = sum(scores) / len(scores) if scores else 0.0
    consistent = avg_score > 0.3  # Threshold: 30% word overlap considered consistent

    return {
        "consistent": consistent,
        "score": round(avg_score, 3),
        "reason": f"Average word overlap: {avg_score:.1%} across {len(responses)} responses",
        "response_count": len(responses),
    }


async def run_multi_turn_conversation(
    target_url: str,
    target_type: str,
    conversation_script: list[dict[str, str]],
    model: str = "",
    timeout: float = 30.0,
) -> dict[str, Any]:
    """
    Execute a multi-turn conversation against the target.
    conversation_script: list of {"role": "user", "content": "..."} dicts.
    Returns the final response and full exchange history.
    """
    history: list[dict[str, str]] = []
    final_response = ""
    errors = []

    for turn in conversation_script:
        if turn.get("role") != "user":
            continue

        message = turn["content"]
        result = await call_target(
            target_url=target_url,
            target_type=target_type,
            message=message,
            model=model,
            timeout=timeout,
        )

        if result.get("error"):
            errors.append(result["error"])
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": f"[ERROR: {result['error']}]"})
        else:
            final_response = result.get("response_text", "")
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": final_response})

    return {
        "final_response": final_response,
        "history": history,
        "errors": errors,
        "turn_count": len([t for t in conversation_script if t.get("role") == "user"]),
    }
