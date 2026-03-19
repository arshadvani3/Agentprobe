-- AgentProbe PostgreSQL schema
-- Run once on first boot (mounted as /docker-entrypoint-initdb.d/init.sql in Compose)

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

CREATE INDEX IF NOT EXISTS idx_evaluations_status ON evaluations(status);
CREATE INDEX IF NOT EXISTS idx_evaluations_created_at ON evaluations(created_at DESC);
