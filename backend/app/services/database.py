"""
PostgreSQL persistence layer via asyncpg.
All evaluation records and events are stored here.
Phase 3 in-memory dict is replaced by this module.
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS evaluations (
    eval_id         TEXT PRIMARY KEY,
    target_url      TEXT NOT NULL,
    target_type     TEXT NOT NULL,
    suite           TEXT NOT NULL,
    depth           TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    overall_score   DOUBLE PRECISION,
    total_tests     INTEGER DEFAULT 0,
    passed          INTEGER DEFAULT 0,
    failed          INTEGER DEFAULT 0,
    report          JSONB,
    events          JSONB NOT NULL DEFAULT '[]',
    request_data    JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_evaluations_created_at ON evaluations(created_at DESC);

CREATE TABLE IF NOT EXISTS custom_suites (
    suite_id        TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    tests           JSONB NOT NULL,
    categories      JSONB NOT NULL DEFAULT '[]',
    test_count      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


async def init_db(postgres_url: str) -> None:
    global _pool
    _pool = await asyncpg.create_pool(postgres_url, min_size=2, max_size=10)
    async with _pool.acquire() as conn:
        await conn.execute(_SCHEMA)
    logger.info("PostgreSQL connected and schema ready")


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL pool closed")


def _get_pool() -> asyncpg.Pool:
    if not _pool:
        raise RuntimeError("Database not initialised — call init_db() first")
    return _pool


def _row_to_dict(row: asyncpg.Record) -> dict[str, Any]:
    d = dict(row)
    # asyncpg returns JSONB as Python objects already; ensure lists/dicts not strings
    for key in ("report", "events", "request_data"):
        if isinstance(d.get(key), str):
            d[key] = json.loads(d[key])
    return d


async def create_evaluation(request_data: dict) -> str:
    eval_id = f"eval_{uuid.uuid4().hex[:8]}"
    pool = _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO evaluations
                (eval_id, target_url, target_type, suite, depth, request_data)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            """,
            eval_id,
            request_data["target_url"],
            request_data["target_type"],
            request_data["suite"],
            request_data["depth"],
            json.dumps(request_data),
        )
    return eval_id


async def get_evaluation(eval_id: str) -> dict[str, Any] | None:
    pool = _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM evaluations WHERE eval_id = $1", eval_id
        )
    return _row_to_dict(row) if row else None


async def list_evaluations() -> list[dict[str, Any]]:
    pool = _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM evaluations ORDER BY created_at DESC"
        )
    return [_row_to_dict(r) for r in rows]


async def update_status(eval_id: str, status: str) -> None:
    pool = _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE evaluations SET status=$1 WHERE eval_id=$2", status, eval_id
        )


_MAX_EVENTS = 2000  # cap per evaluation — prevents unbounded JSONB growth


async def append_event(eval_id: str, event: dict) -> None:
    """Append a single event; sliding-window trim to _MAX_EVENTS entries."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE evaluations
            SET events = (
                SELECT jsonb_agg(e)
                FROM (
                    SELECT e
                    FROM jsonb_array_elements(events || $1::jsonb) AS e
                    OFFSET GREATEST(0, jsonb_array_length(events) + 1 - $3)
                ) sub
            )
            WHERE eval_id = $2
            """,
            json.dumps([event]),
            eval_id,
            _MAX_EVENTS,
        )


async def set_report(
    eval_id: str,
    report: dict,
    overall_score: float,
    total: int,
    passed: int,
    failed: int,
) -> None:
    pool = _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE evaluations
            SET report=$1::jsonb, overall_score=$2, total_tests=$3, passed=$4, failed=$5
            WHERE eval_id=$6
            """,
            json.dumps(report),
            overall_score,
            total,
            passed,
            failed,
            eval_id,
        )


_ALLOWED_UPDATE_COLS = frozenset({
    "status", "overall_score", "completed_at",
    "total_tests", "passed", "failed", "report",
})


async def update_fields(eval_id: str, **kwargs: Any) -> None:
    """Generic field updater — used by demo runner for ad-hoc updates."""
    if not kwargs:
        return
    for col in kwargs:
        if col not in _ALLOWED_UPDATE_COLS:
            raise ValueError(f"update_fields: column '{col}' is not in the allowed list")
    pool = _get_pool()
    cols = ", ".join(f"{k}=${i + 2}" for i, k in enumerate(kwargs))
    values = list(kwargs.values())
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE evaluations SET {cols} WHERE eval_id=$1",
            eval_id,
            *values,
        )


async def complete_evaluation(eval_id: str, status: str = "complete") -> None:
    pool = _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE evaluations SET status=$1, completed_at=$2 WHERE eval_id=$3",
            status,
            datetime.now(timezone.utc),
            eval_id,
        )


# ---------------------------------------------------------------------------
# Custom suites
# ---------------------------------------------------------------------------

async def create_custom_suite(
    name: str,
    description: str,
    tests: list[dict],
    categories: list[str],
) -> str:
    suite_id = f"cs_{uuid.uuid4().hex[:8]}"
    pool = _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO custom_suites
                (suite_id, name, description, tests, categories, test_count)
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6)
            """,
            suite_id,
            name,
            description,
            json.dumps(tests),
            json.dumps(categories),
            len(tests),
        )
    return suite_id


async def list_custom_suites() -> list[dict[str, Any]]:
    pool = _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT suite_id, name, description, categories, test_count, created_at "
            "FROM custom_suites ORDER BY created_at DESC"
        )
    result = []
    for row in rows:
        d = dict(row)
        if isinstance(d.get("categories"), str):
            d["categories"] = json.loads(d["categories"])
        result.append(d)
    return result


async def get_custom_suite(suite_id: str) -> dict[str, Any] | None:
    pool = _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM custom_suites WHERE suite_id = $1", suite_id
        )
    if not row:
        return None
    d = dict(row)
    for key in ("tests", "categories"):
        if isinstance(d.get(key), str):
            d[key] = json.loads(d[key])
    return d


async def get_metrics() -> dict[str, int]:
    """Return evaluation counts using efficient COUNT queries — not a full scan."""
    pool = _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(*)                                                   AS total,
                COUNT(*) FILTER (WHERE status = 'complete')               AS complete,
                COUNT(*) FILTER (WHERE status = 'error')                  AS error,
                COUNT(*) FILTER (WHERE status NOT IN ('complete','error','pending')) AS running
            FROM evaluations
            """
        )
    return {
        "evaluations_total": row["total"],
        "evaluations_complete": row["complete"],
        "evaluations_running": row["running"],
        "evaluations_error": row["error"],
    }


async def delete_custom_suite(suite_id: str) -> bool:
    pool = _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM custom_suites WHERE suite_id = $1", suite_id
        )
    try:
        return int(result.split()[-1]) > 0
    except (IndexError, ValueError):
        return False
