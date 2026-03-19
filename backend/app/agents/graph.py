from langgraph.graph import StateGraph, END

from .state import EvalState
from .supervisor import supervisor_node
from .scenario_generator import scenario_generator_node
from .security_agent import security_agent_node
from .consistency_agent import consistency_agent_node
from .executor import executor_node
from .evaluator import evaluator_node
from .report_generator import report_generator_node


def should_regenerate(state: EvalState) -> str:
    """Conditional edge after evaluator: regenerate harder tests or write report."""
    evaluations = state.get("evaluations", [])
    iteration = state.get("iteration", 0)

    if not evaluations or iteration >= 2:
        return "report_generator"

    passed = sum(1 for e in evaluations if e.get("passed", False))
    pass_rate = passed / len(evaluations) if evaluations else 0

    if pass_rate > 0.90 and iteration < 2:
        return "supervisor_retry"

    return "report_generator"


def supervisor_routing(state: EvalState) -> str:
    """After supervisor runs, decide what to do next."""
    iteration = state.get("iteration", 0)
    # If this is a retry (iteration > 0), only regenerate scenarios
    if iteration > 0:
        return "scenario_generator"
    return "scenario_generator"


def build_graph() -> StateGraph:
    graph = StateGraph(EvalState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("scenario_generator", scenario_generator_node)
    graph.add_node("security_agent", security_agent_node)
    graph.add_node("consistency_agent", consistency_agent_node)
    graph.add_node("executor", executor_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("report_generator", report_generator_node)

    # Start with supervisor
    graph.set_entry_point("supervisor")

    # Supervisor → scenario generator (sequence)
    graph.add_edge("supervisor", "scenario_generator")

    # Scenario generator → security agent → consistency agent (sequence)
    graph.add_edge("scenario_generator", "security_agent")
    graph.add_edge("security_agent", "consistency_agent")

    # All generators → executor
    graph.add_edge("consistency_agent", "executor")

    # Executor → evaluator
    graph.add_edge("executor", "evaluator")

    # Evaluator → conditional: report or retry
    graph.add_conditional_edges(
        "evaluator",
        should_regenerate,
        {
            "report_generator": "report_generator",
            "supervisor_retry": "supervisor",
        },
    )

    # Report generator → end
    graph.add_edge("report_generator", END)

    return graph.compile()


# Compiled graph — import this to run
app = build_graph()
