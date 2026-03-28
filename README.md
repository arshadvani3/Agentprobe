# AgentProbe

**Multi-agent AI evaluation platform.** Point AgentProbe at any AI agent's HTTP API and a coordinated team of specialized agents stress-tests it for failures, hallucinations, prompt injection vulnerabilities, and reliability issues — then delivers a structured, quantified evaluation report.

**Live demo →** [agentprobe-psi.vercel.app](https://agentprobe-psi.vercel.app)

---

## What It Does

AgentProbe runs a directed, adaptive evaluation pipeline against any AI agent — no access to internals required. It operates entirely over HTTP, making it compatible with any model or service that exposes a chat-style API.

The pipeline runs seven coordinated agents:

| Agent | Responsibility |
|-------|---------------|
| **Supervisor** | Plans test strategy; re-dispatches with harder tests if initial pass rate exceeds 90% |
| **Scenario Generator** | LLM-generated test cases: happy path, edge cases, adversarial inputs, hallucination traps, out-of-scope queries |
| **Security Agent** | 25-pattern injection battery: prompt injection, jailbreaks, system prompt extraction attempts |
| **Consistency Agent** | Paraphrase equivalence checks, multi-turn context coherence |
| **Executor** | Async HTTP calls to target; supports Ollama, OpenAI-compatible, and generic REST formats |
| **Evaluator** | LLM-as-judge scoring: accuracy, relevance, hallucination, safety, helpfulness (each 0–1) |
| **Report Generator** | Synthesizes scores into a structured report with a written narrative |

Each response is scored on five dimensions and aggregated into a single overall score. Security injections that succeed force the safety score to 0.

---

## Architecture

```
                    ┌──────────────────────────────────────────┐
                    │            LangGraph Eval Graph           │
                    │                                           │
  HTTP API  ──────► │  Supervisor ──► Scenario Generator        │
  (target           │       │                                   │
   agent)           │       ├──► Security Agent  ──┐           │
                    │       │                       ▼           │
                    │       └──► Consistency Agent ─► Executor  │
                    │                               │           │
                    │                               ▼           │
                    │                           Evaluator       │
                    │                         (LLM judge)       │
                    │                               │           │
                    │                               ▼           │
                    │                      Report Generator     │
                    └───────────────────────────────┬──────────┘
                                                    │
                    Events ──► Redis pub/sub ──► WebSocket ──► React Dashboard
                    Results ──► PostgreSQL (persistent)
                    Test cases ──► ChromaDB (semantic deduplication)
```

**Two LLM roles — strictly separated:**
- **Target** — the agent under test (your Ollama instance, Groq endpoint, OpenAI API, or any HTTP API)
- **Judge** — an independent Ollama or Groq instance that scores responses; never the same model being evaluated

---

## Quick Start

### Option 1: Docker Compose (recommended)

```bash
git clone https://github.com/arshadvani/agentprobe
cd agentprobe

cp .env.example .env
# Edit .env if needed — defaults work for local Ollama

docker compose up
```

| Service | URL |
|---------|-----|
| Frontend dashboard | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

Requires Ollama running on the host (`ollama serve`) for real evaluations. **Demo mode works without any LLM.**

---

### Option 2: Local Development

**Backend**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start Postgres + Redis
docker compose up postgres redis -d

# Start backend
uvicorn backend.app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

---

## Running Evaluations

### Demo mode — no LLM required
Check **Demo Mode** in the form. Runs 26 pre-canned tests in ~30 seconds and exercises the full UI: live agent graph, event feed, score radar, and generated report.

### Against a local Ollama instance
```
Target URL:   http://localhost:11434
Target Type:  ollama
Model:        llama3.1:8b
```

### Against Groq or any OpenAI-compatible API
```
Target URL:   https://api.groq.com/openai/v1
Target Type:  openai
Model:        llama-3.1-8b-instant
API Key:      gsk_...
```

### Custom test suites
Upload a `.py` test file via the **Custom Test Suite** panel. AgentProbe merges your cases with the standard suite. A starter template is available for download directly from the UI.

---

## API Reference

```bash
# Start an evaluation
curl -X POST http://localhost:8000/api/v1/evaluations \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://localhost:11434",
    "target_type": "ollama",
    "suite": "general_chatbot",
    "depth": "standard",
    "model": "llama3.1:8b"
  }'

# List all evaluations
curl http://localhost:8000/api/v1/evaluations

# Get full report
curl http://localhost:8000/api/v1/evaluations/{eval_id}/report

# Health check (returns Postgres + Redis status)
curl http://localhost:8000/health
```

**WebSocket event stream:**
```
ws://localhost:8000/api/v1/stream/{eval_id}
```

Events are emitted in real time as the graph executes. Each event carries an agent name, type, and payload — consumed live by the dashboard.

---

## Scoring

| Dimension | What it measures |
|-----------|-----------------|
| **Accuracy** | Factual correctness of the response |
| **Relevance** | Whether the response addresses the question |
| **Hallucination** | 1.0 = no hallucination detected |
| **Safety** | Harmful or policy-violating content (0 = failed) |
| **Helpfulness** | Practical utility of the response |

Pass threshold: overall score ≥ 0.6. Prompt injection successes override the safety score to 0 regardless of other dimensions.

---

## Tech Stack

| Layer | Technology | Decision rationale |
|-------|-----------|-------------------|
| Agent orchestration | **LangGraph** | Conditional graph routing enables adaptive test depth — sequential or parallel pipelines cannot do this |
| LLM judge | **Ollama / Groq** | Judge is independent from target; configurable between local Ollama and Groq API |
| Backend | **FastAPI** + asyncio | Fully async — concurrent target calls and WebSocket streaming without blocking |
| Event streaming | **Redis** pub/sub | Decouples the eval graph from WebSocket consumers; late-connecting clients replay from Postgres |
| Persistence | **PostgreSQL** + asyncpg | Raw asyncpg driver — no ORM overhead; JSONB for report blobs, indexed on `created_at` |
| Vector store | **ChromaDB** | Semantic deduplication of test cases across runs |
| Frontend | **React 18** + TypeScript + Vite | Strict TypeScript; zero-error build |
| Graph visualization | **React Flow** | Live agent execution graph with active/complete node states |
| Charts | **Recharts** | Radar chart for per-dimension score breakdown |
| Containers | **Docker** + Compose | Single `docker compose up` brings up all four services |
| Kubernetes | **GKE manifests** | Deployment, Service, PVC, ConfigMap, Secrets definitions in `k8s/` |
| CI | **GitHub Actions** | Backend lint + pytest, frontend TypeScript build, Docker image build |

---

## Environment Variables

```bash
# ── LLM Judge ─────────────────────────────────────────────────────
# Option A: Groq (recommended for cloud deployments)
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant

# Option B: Local Ollama (used when GROQ_API_KEY is not set)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# ── Databases ──────────────────────────────────────────────────────
POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/agentprobe
REDIS_URL=redis://localhost:6379
CHROMADB_PATH=./data/chromadb

# ── Auth (leave empty to disable in development) ───────────────────
AGENTPROBE_API_KEY=

# ── CORS ───────────────────────────────────────────────────────────
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

LOG_LEVEL=INFO
```

---

## Project Structure

```
agentprobe/
├── backend/
│   ├── app/
│   │   ├── agents/          # 7 LangGraph agent nodes + prompt .txt files
│   │   ├── api/             # FastAPI routers — evaluations, stream, health, custom suites
│   │   ├── core/            # settings.py (Pydantic BaseSettings), auth.py
│   │   ├── models/          # Pydantic request/response schemas
│   │   ├── services/        # database.py, redis_client.py, chroma_store.py, demo_runner.py
│   │   └── tools/           # target_caller.py, scoring.py, injection_battery.py
│   ├── db/init.sql          # PostgreSQL schema
│   ├── test_suites/         # YAML test suites (general_chatbot, injection_patterns)
│   └── tests/               # pytest integration tests
├── frontend/
│   └── src/
│       ├── components/      # AgentGraph, EventFeed, ScoreChart, ScoreGauge, EvaluationDetail, …
│       └── hooks/           # useEvaluations (REST + polling), useEventStream (WebSocket)
├── k8s/                     # Kubernetes manifests (deployment, service, configmap, secrets)
├── .github/workflows/       # CI pipeline
├── docker-compose.yml
└── .env.example
```

---

## Security

- **SSRF protection** — `target_url` is validated against private and reserved IP ranges (RFC 1918, link-local, loopback) before any HTTP request is made
- **Timing-safe auth** — API key comparison uses `secrets.compare_digest()` to prevent timing side-channel attacks
- **WebSocket authentication** — when `AGENTPROBE_API_KEY` is set, WebSocket connections require a matching `?token=` query parameter
- **Sandboxed exec** — custom test suite files are executed via `RestrictedPython` (bytecode-level guards) rather than bare `exec()`
- **Rate limiting** — evaluation start endpoint is limited to 10 requests/minute per IP via `slowapi`
- **Security headers** — nginx serves `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, and `Referrer-Policy` on all responses

---

## License

MIT
