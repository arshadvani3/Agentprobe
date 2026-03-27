from datetime import datetime, timezone

from fastapi import APIRouter

from ..services import database, redis_client

router = APIRouter()


@router.get("/ping")
async def ping() -> dict:
    """Instant liveness check — no DB/Redis queries. Used by Railway healthcheck."""
    return {"status": "ok"}


@router.get("/health")
async def health() -> dict:
    """Liveness + dependency health check."""
    checks: dict[str, str] = {}

    # PostgreSQL — never expose connection URL in response
    try:
        pool = database._get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        checks["postgres"] = "ok"
    except Exception as e:
        # Redact credentials from error — Postgres errors often include the URL
        msg = str(e)
        for part in ("postgresql://", "postgres://"):
            if part in msg:
                msg = "connection failed (check POSTGRES_URL)"
                break
        checks["postgres"] = f"error: {msg}"

    # Redis
    try:
        client = redis_client.get_client()
        await client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


@router.get("/metrics")
async def metrics() -> dict:
    """Basic evaluation metrics — uses COUNT queries, not full table scan."""
    try:
        counts = await database.get_metrics()
        return counts
    except Exception as e:
        return {"error": str(e)}
