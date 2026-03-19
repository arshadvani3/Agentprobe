from pathlib import Path

import yaml
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ..core.auth import verify_api_key
from ..models.schemas import (
    EvaluationDetail,
    EvaluationSummary,
    StartEvaluationRequest,
    TestSuiteInfo,
)
from ..services.demo_runner import run_demo_evaluation
from ..services.evaluation_store import (
    create_evaluation,
    get_evaluation,
    list_evaluations,
    run_evaluation,
)
from ..tools.target_caller import _call_ollama, _call_openai_compatible, _call_simple_endpoint

router = APIRouter(prefix="/api/v1", dependencies=[Depends(verify_api_key)])

_SUITES_DIR = Path(__file__).parent.parent.parent / "test_suites"


def _record_to_summary(record: dict) -> EvaluationSummary:
    return EvaluationSummary(
        eval_id=record["eval_id"],
        target_url=record["target_url"],
        target_type=record["target_type"],
        suite=record["suite"],
        depth=record["depth"],
        status=record["status"],
        created_at=record["created_at"],
        completed_at=record.get("completed_at"),
        overall_score=record.get("overall_score"),
        total_tests=record.get("total_tests", 0),
        passed=record.get("passed", 0),
        failed=record.get("failed", 0),
    )


@router.post("/evaluations", response_model=EvaluationSummary, status_code=202)
async def start_evaluation(
    request: StartEvaluationRequest,
    background_tasks: BackgroundTasks,
) -> EvaluationSummary:
    """Start a new evaluation. Returns immediately; eval runs in background."""
    req = request.model_dump()

    # Demo mode: skip pre-flight and LLM calls entirely
    if request.demo:
        eval_id = await create_evaluation(req)
        background_tasks.add_task(run_demo_evaluation, eval_id, req)
        record = await get_evaluation(eval_id)
        return _record_to_summary(record)

    # Real mode: connectivity check first
    if request.target_type == "ollama":
        result = await _call_ollama(request.target_url, request.model, "ping", 10.0)
    elif request.target_type == "openai":
        result = await _call_openai_compatible(
            request.target_url,
            [{"role": "user", "content": "ping"}],
            request.model or "gpt-3.5-turbo",
            10.0,
            api_key=request.api_key,
        )
    else:
        result = await _call_simple_endpoint(request.target_url, "ping", 10.0)

    if result["error"]:
        raise HTTPException(
            status_code=422,
            detail=f"Target agent unreachable: {result['error']}",
        )

    eval_id = await create_evaluation(req)
    background_tasks.add_task(run_evaluation, eval_id, req)
    record = await get_evaluation(eval_id)
    return _record_to_summary(record)


@router.get("/evaluations", response_model=list[EvaluationSummary])
async def list_evals() -> list[EvaluationSummary]:
    return [_record_to_summary(r) for r in await list_evaluations()]


@router.get("/evaluations/{eval_id}", response_model=EvaluationDetail)
async def get_eval(eval_id: str) -> EvaluationDetail:
    record = await get_evaluation(eval_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Evaluation {eval_id} not found")
    summary = _record_to_summary(record)
    return EvaluationDetail(**summary.model_dump(), report=None, test_count=record.get("total_tests", 0))


@router.get("/evaluations/{eval_id}/report", response_model=dict)
async def get_report(eval_id: str) -> dict:
    record = await get_evaluation(eval_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Evaluation {eval_id} not found")
    if not record.get("report"):
        raise HTTPException(status_code=404, detail="Report not ready yet")
    return record["report"]


@router.get("/test-suites", response_model=list[TestSuiteInfo])
async def list_test_suites() -> list[TestSuiteInfo]:
    suites = []
    for path in sorted(_SUITES_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text())
            tests = data.get("tests", [])
            categories = list({t.get("category", "unknown") for t in tests})
            suites.append(TestSuiteInfo(
                name=data.get("name", path.stem),
                description=data.get("description", ""),
                test_count=len(tests),
                categories=sorted(categories),
            ))
        except Exception:
            continue
    return suites
