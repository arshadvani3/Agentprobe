"""
AgentProbe CLI — Phase 1 entry point.

Usage:
    python -m agentprobe --target http://localhost:11434/api/chat --suite general_chatbot
    python -m agentprobe --target http://localhost:11434/api/chat --depth quick
    python -m agentprobe --target http://api.example.com/chat --categories happy_path,edge_cases
"""
import argparse
import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path

# Ensure the parent directory is on the path when running as python -m agentprobe
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402 — optional, graceful if not installed
load_dotenv()  # Load .env if it exists

from backend.app.agents.graph import app as graph  # noqa: E402
from backend.app.agents.state import EvalState  # noqa: E402
from backend.app.tools.target_caller import _call_ollama, _call_openai_compatible, _call_simple_endpoint  # noqa: E402


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _print_banner(target: str, suite: str) -> None:
    print("\n" + "═" * 51)
    print("  AgentProbe — AI Agent Stress Tester")
    print("═" * 51)
    print(f"  Target : {target}")
    print(f"  Suite  : {suite}")
    print("═" * 51 + "\n")


def _warn_symbol(score: float) -> str:
    return " ⚠️" if score < 0.6 else ""


def _print_report(report: dict, target: str) -> None:
    summary = report.get("summary", {})
    cat_breakdown = report.get("category_breakdown", {})
    dim_scores = report.get("dimension_scores", {})
    security_findings = report.get("security_findings", [])
    top_failures = report.get("top_failures", [])
    narrative = report.get("narrative", "")

    total = summary.get("total_tests", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    overall = summary.get("overall_score", 0.0)

    print("\n" + "═" * 51)
    print("  AgentProbe Evaluation Report")
    print(f"  Target: {target}")
    print(f"  Tests: {total} | Passed: {passed} | Failed: {failed}")
    print("═" * 51)
    print(f"\n  Overall Score: {overall:.2f} / 1.0\n")

    if cat_breakdown:
        print("  Category Breakdown:")
        for cat, stats in sorted(cat_breakdown.items()):
            name = cat.replace("_", " ").title()
            cat_score = stats.get("avg_overall", 0.0)
            cat_passed = stats.get("passed", 0)
            cat_total = stats.get("total", 0)
            warn = _warn_symbol(cat_score)
            print(f"    {name:<22} {cat_score:.2f}  ({cat_passed}/{cat_total} passed){warn}")

    if dim_scores:
        print("\n  Dimension Scores:")
        for dim, score in sorted(dim_scores.items()):
            name = dim.replace("_", " ").title()
            warn = _warn_symbol(score)
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            print(f"    {name:<15} {bar}  {score:.2f}{warn}")

    if security_findings:
        print("\n  🔴 Security Findings:")
        for finding in security_findings:
            print(f"    - {finding}")
    else:
        print("\n  ✅ No security vulnerabilities detected.")

    if top_failures:
        print(f"\n  Top Failures (worst {min(len(top_failures), 10)}):")
        for i, failure in enumerate(top_failures[:10], 1):
            cat = failure.get("category", "unknown")
            input_preview = failure.get("input", "")[:60].replace("\n", " ")
            reason = failure.get("failure_reason", "")
            score = failure.get("scores", {}).get("overall", 0)
            print(f"    {i:2}. [{cat}] \"{input_preview}...\" → {reason} (score: {score:.2f})")

    if narrative:
        print("\n  Narrative Report:")
        print("  " + "-" * 47)
        for line in narrative.split("\n"):
            print(f"  {line}")

    print("\n" + "═" * 51 + "\n")


async def _preflight_check(target: str, target_type: str, model: str, timeout: float) -> dict:
    """Make one test call to verify the target is reachable."""
    if target_type == "ollama":
        return await _call_ollama(target, model, "Hello", timeout)
    elif target_type == "openai":
        return await _call_openai_compatible(target, [{"role": "user", "content": "Hello"}], model, timeout)
    else:
        return await _call_simple_endpoint(target, "Hello", timeout)


async def run(
    target: str,
    suite: str,
    categories: list[str] | None,
    depth: str,
    target_type: str,
    model: str,
    timeout: float,
) -> dict:
    eval_id = f"eval_{uuid.uuid4().hex[:8]}"

    initial_state: EvalState = {
        "config": {
            "eval_id": eval_id,
            "target_url": target,
            "target_type": target_type,
            "suite": suite,
            "categories": categories,
            "depth": depth,
            "model": model,
            "timeout": timeout,
            "target_description": f"A general AI agent accessible at {target}",
        },
        "test_plan": [],
        "test_cases": [],
        "security_tests": [],
        "consistency_tests": [],
        "execution_results": [],
        "evaluations": [],
        "report": {},
        "agent_messages": [],
        "iteration": 0,
        "status": "planning",
    }

    print("  Running evaluation... (this may take several minutes)\n")

    last_status = ""
    final_state = None

    async for chunk in graph.astream(initial_state, stream_mode="updates"):
        for node_name, updates in chunk.items():
            status = updates.get("status", "")
            messages = updates.get("agent_messages", [])
            for msg in messages:
                evt_type = msg.get("type", "")
                data = msg.get("data", {})
                agent = msg.get("agent", node_name)

                if evt_type == "plan_created":
                    print(f"  [supervisor]    Test plan created: {len(data.get('test_plan', []))} categories")
                elif evt_type == "tests_generated":
                    print(f"  [scenario]      Generated {data.get('count', 0)} test cases")
                elif evt_type == "security_finding":
                    print(f"  [security]      Loaded {data.get('security_test_count', 0)} security tests")
                elif evt_type == "consistency_result":
                    print(f"  [consistency]   Created {data.get('consistency_test_count', 0)} consistency tests")
                elif evt_type == "test_executed":
                    total = data.get("total", 0)
                    executed = data.get("executed", 0)
                    errors = data.get("errors", 0)
                    print(f"  [executor]      Executed {executed}/{total} tests ({errors} errors)")
                elif evt_type == "test_evaluated":
                    t = data.get("total", 0)
                    p = data.get("passed", 0)
                    f = data.get("failed", 0)
                    print(f"  [evaluator]     Evaluated {t} tests: {p} passed, {f} failed")
                elif evt_type == "report_ready":
                    score = data.get("overall_score", 0)
                    print(f"  [report]        Report ready — overall score: {score:.2f}")
                elif evt_type == "error":
                    print(f"  [ERROR]         {data.get('message', 'Unknown error')}")

            final_state = updates

    return final_state or {}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AgentProbe — AI Agent Stress Tester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m agentprobe --target http://localhost:11434/api/chat --suite general_chatbot
  python -m agentprobe --target http://api.mybot.com/chat --depth quick --type openai
  python -m agentprobe --target http://localhost:8080/chat --categories happy_path,edge_cases
        """,
    )
    parser.add_argument("--target", required=True, help="Target agent API URL")
    parser.add_argument("--suite", default="general_chatbot", help="Test suite name (default: general_chatbot)")
    parser.add_argument("--categories", default=None, help="Comma-separated list of categories to run")
    parser.add_argument("--depth", choices=["quick", "standard", "deep"], default="standard", help="Test depth (default: standard)")
    parser.add_argument("--type", dest="target_type", choices=["ollama", "openai", "simple"], default="ollama", help="Target API type (default: ollama)")
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", ""), help="Model name for target (default: OLLAMA_MODEL env var)")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds (default: 30)")
    parser.add_argument("--log-level", default="WARNING", help="Log level (default: WARNING)")
    parser.add_argument("--output", default=None, help="Save JSON report to this file path")

    args = parser.parse_args()

    _setup_logging(args.log_level)
    _print_banner(args.target, args.suite)

    categories = [c.strip() for c in args.categories.split(",")] if args.categories else None

    if args.target_type == "ollama" and not args.model:
        print("  ⚠️  No --model specified. Defaulting to 'llama3.1:8b'.")
        print("     Run `ollama list` to see available models.\n")
        args.model = "llama3.1:8b"

    # Pre-flight: verify target is reachable before running full eval
    print("  Checking target connectivity...")
    preflight = asyncio.run(_preflight_check(args.target, args.target_type, args.model, args.timeout))
    if preflight["error"]:
        print(f"  ❌ Target unreachable: {preflight['error']}")
        print("  Fix the connection issue before running a full evaluation.")
        sys.exit(1)
    else:
        print(f"  ✅ Target reachable (got {len(preflight['response_text'])} chars in {preflight['latency_ms']:.0f}ms)\n")

    try:
        final_state = asyncio.run(
            run(
                target=args.target,
                suite=args.suite,
                categories=categories,
                depth=args.depth,
                target_type=args.target_type,
                model=args.model,
                timeout=args.timeout,
            )
        )
    except ConnectionError as e:
        print(f"\n  ❌ Connection Error: {e}")
        print("  Make sure Ollama is running: ollama serve")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n  Evaluation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n  ❌ Unexpected error: {e}")
        logging.exception("Unexpected error during evaluation")
        sys.exit(1)

    report = final_state.get("report", {})
    if not report:
        print("\n  ❌ No report generated. Check logs for errors.")
        sys.exit(1)

    _print_report(report, args.target)

    if args.output:
        import json
        out_path = Path(args.output)
        out_path.write_text(json.dumps(report, indent=2, default=str))
        print(f"  Report saved to: {out_path}\n")


if __name__ == "__main__":
    main()
