import operator
from typing import Annotated, TypedDict


class EvalState(TypedDict):
    config: dict                                              # {target_url, target_type, categories, depth, suite}
    test_plan: list[str]                                      # Supervisor's plan
    test_cases: Annotated[list[dict], operator.add]           # Generated scenario tests
    security_tests: Annotated[list[dict], operator.add]       # Security/injection tests
    consistency_tests: Annotated[list[dict], operator.add]    # Consistency tests
    execution_results: Annotated[list[dict], operator.add]    # Raw execution results
    evaluations: Annotated[list[dict], operator.add]          # LLM-judged evaluations
    report: dict                                              # Final report
    agent_messages: Annotated[list[dict], operator.add]       # Event log from all agents
    iteration: int                                            # How many supervisor loops
    status: str                                               # planning | generating | executing | evaluating | complete
