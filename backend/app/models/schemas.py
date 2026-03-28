from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TargetType(str, Enum):
    ollama = "ollama"
    openai = "openai"
    simple = "simple"


class EvalDepth(str, Enum):
    quick = "quick"
    standard = "standard"
    deep = "deep"


class EvalStatus(str, Enum):
    pending = "pending"
    planning = "planning"
    generating = "generating"
    executing = "executing"
    evaluating = "evaluating"
    complete = "complete"
    error = "error"


# ── Request ──────────────────────────────────────────────────────────────────

class StartEvaluationRequest(BaseModel):
    target_url: str = Field(
        ...,
        description="URL of the agent to test",
        min_length=10,
        max_length=2048,
    )
    target_type: TargetType = Field(TargetType.ollama, description="API format of the target")
    model: str = Field("", description="Model name (required for ollama targets)")
    suite: str = Field("general_chatbot", description="Test suite name")
    categories: list[str] | None = Field(None, description="Specific categories to run")
    depth: EvalDepth = Field(EvalDepth.standard, description="Test depth")
    timeout: float = Field(30.0, description="Per-request timeout in seconds")
    target_description: str = Field(
        "A general-purpose AI assistant",
        description="Short description of the target agent (used to generate relevant test cases)",
    )
    api_key: str = Field("", description="Bearer token / API key for the target (e.g. Groq, OpenAI)")
    demo: bool = Field(False, description="Run a fast demo with pre-canned results (no LLM calls)")
    custom_suite_id: str | None = Field(
        None,
        description="ID of an uploaded custom test suite — tests are run alongside the selected suite",
    )


# ── Response ─────────────────────────────────────────────────────────────────

class EvaluationSummary(BaseModel):
    eval_id: str
    target_url: str
    target_type: str
    suite: str
    depth: str
    status: EvalStatus
    created_at: datetime
    completed_at: datetime | None = None
    overall_score: float | None = None
    total_tests: int = 0
    passed: int = 0
    failed: int = 0


class ScoreDimensions(BaseModel):
    accuracy: float
    relevance: float
    hallucination: float
    safety: float
    helpfulness: float
    overall: float


class TestResult(BaseModel):
    test_id: str
    input: str
    response: str
    latency_ms: float
    scores: ScoreDimensions | None = None
    passed: bool
    category: str
    subcategory: str = ""
    failure_reason: str = ""
    reasoning: str = ""


class CategoryStats(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float
    avg_overall: float


class EvaluationReport(BaseModel):
    eval_id: str
    target_url: str
    generated_at: datetime
    summary: dict[str, Any]
    category_breakdown: dict[str, CategoryStats]
    dimension_scores: ScoreDimensions | None = None
    security_findings: list[str]
    top_failures: list[dict[str, Any]]
    narrative: str


class EvaluationDetail(EvaluationSummary):
    report: EvaluationReport | None = None
    test_count: int = 0


class TestSuiteInfo(BaseModel):
    name: str
    description: str
    test_count: int
    categories: list[str]


class CustomSuiteInfo(BaseModel):
    suite_id: str
    name: str
    description: str
    test_count: int
    categories: list[str]


class AgentEvent(BaseModel):
    event_id: str
    eval_id: str
    agent: str
    type: str
    data: dict[str, Any]
    timestamp: str
