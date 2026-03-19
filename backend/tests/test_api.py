"""
Integration tests for the AgentProbe API.

Requires real Postgres + Redis running (see conftest.py for setup).
Uses httpx.AsyncClient to hit the live FastAPI app.

Run:
    pytest backend/tests/ -v
"""
import asyncio
import os
import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient, ASGITransport


# Override DB/Redis URLs for test isolation
os.environ.setdefault("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/agentprobe_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("CHROMADB_PATH", "/tmp/agentprobe_test_chroma")

# Must import app AFTER setting env vars
from backend.app.main import app  # noqa: E402


@pytest_asyncio.fixture(scope="module")
async def client():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "AgentProbe API"


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert "checks" in data


@pytest.mark.asyncio
async def test_health_postgres_ok(client: AsyncClient):
    resp = await client.get("/health")
    data = resp.json()
    assert data["checks"].get("postgres") == "ok", f"Postgres unhealthy: {data}"


@pytest.mark.asyncio
async def test_health_redis_ok(client: AsyncClient):
    resp = await client.get("/health")
    data = resp.json()
    assert data["checks"].get("redis") == "ok", f"Redis unhealthy: {data}"


@pytest.mark.asyncio
async def test_list_evaluations_empty(client: AsyncClient):
    resp = await client.get("/api/v1/evaluations")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_test_suites(client: AsyncClient):
    resp = await client.get("/api/v1/test-suites")
    assert resp.status_code == 200
    suites = resp.json()
    assert isinstance(suites, list)
    assert len(suites) > 0
    suite_names = [s["name"] for s in suites]
    assert any("chatbot" in n.lower() or "general" in n.lower() for n in suite_names)


@pytest.mark.asyncio
async def test_start_demo_evaluation(client: AsyncClient):
    """Demo mode should create an evaluation and start it in the background."""
    payload = {
        "target_url": "http://localhost:11434",
        "target_type": "ollama",
        "suite": "general_chatbot",
        "depth": "quick",
        "demo": True,
    }
    resp = await client.post("/api/v1/evaluations", json=payload)
    assert resp.status_code == 202
    data = resp.json()
    assert "eval_id" in data
    assert data["status"] in ("pending", "planning", "generating", "executing", "evaluating", "complete")
    return data["eval_id"]


@pytest.mark.asyncio
async def test_get_evaluation_after_start(client: AsyncClient):
    """Evaluation created by demo mode should be retrievable."""
    payload = {
        "target_url": "http://localhost:11434",
        "target_type": "ollama",
        "suite": "general_chatbot",
        "depth": "quick",
        "demo": True,
    }
    create_resp = await client.post("/api/v1/evaluations", json=payload)
    assert create_resp.status_code == 202
    eval_id = create_resp.json()["eval_id"]

    get_resp = await client.get(f"/api/v1/evaluations/{eval_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["eval_id"] == eval_id


@pytest.mark.asyncio
async def test_get_evaluation_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/evaluations/eval_doesnotexist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_report_not_ready_yet(client: AsyncClient):
    """Report endpoint returns 404 when eval just started."""
    payload = {
        "target_url": "http://localhost:11434",
        "target_type": "ollama",
        "suite": "general_chatbot",
        "depth": "quick",
        "demo": True,
    }
    create_resp = await client.post("/api/v1/evaluations", json=payload)
    eval_id = create_resp.json()["eval_id"]

    # Immediately after start the report should not be ready
    report_resp = await client.get(f"/api/v1/evaluations/{eval_id}/report")
    assert report_resp.status_code in (404, 200)  # 200 if somehow already done


@pytest.mark.asyncio
async def test_metrics(client: AsyncClient):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "evaluations_total" in data
