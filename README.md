# AgentProbe

**Multi-agent AI stress-testing platform.** Point it at any AI agent's HTTP API and a team of specialized agents red-teams it for failures, hallucinations, security vulnerabilities, and reliability issues — then generates a quantified evaluation report.

Built as a portfolio project targeting AI/ML engineering roles. Every architectural decision is intentional and explainable.

---

## Demo

Run a full evaluation in ~30 seconds with no LLM calls needed:

```bash
docker compose up -d
# Open http://localhost:5173 → check "Demo Mode" → Start Evaluation
```

---

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           LangGraph Eval Graph           │
                    │                                          │
  HTTP API  ──────► │  Supervisor ──► Scenario Generator       │
  (target           │       │                                  │
   agent)           │       ├──► Security Agent  ──┐          │
                    │       │                       ▼          │
                    │       └──► Consistency Agent ─► Executor │
                    │                               │          │
                    │                               ▼          │
                    │                           Evaluator      │
                    │                           (Ollama judge) │
                    │                               │          │
                    │                               ▼          │
                    │                      Report Generator    │
                    └───────────────────────────────┬─────────┘
                                                    │
                    Events ──► Redis pub/sub ──► WebSocket ──► React Dashboard
                    Results ──► PostgreSQL (persisted)
                    Test cases ──► ChromaDB (deduplicated)
```

**Two LLM roles — deliberately separated:**
- **Target** — the AI being tested (your Ollama, Groq, OpenAI endpoint, or any HTTP API)
- **Judge** — local Ollama (Llama 3.1 8B) scores responses independently

---

## Quick Start

### Option 1: Docker Compose (recommended)

```bash
git clone https://github.com/yourname/agentprobe
cd agentprobe

cp .env.example .env
# Edit .env if needed (defaults work for local Ollama)

docker compose up
```

- Backend API: http://localhost:8000
- Frontend dashboard: http://localhost:5173
- API docs: http://localhost:8000/docs

Requires Ollama running on the host (`ollama serve`) for real evaluations. Demo mode works without it.

### Option 2: Local dev

**Backend**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start Postgres + Redis via Docker
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

### Demo mode (no LLM needed)
Check **Demo Mode** in the form. Runs 26 pre-canned tests in ~30s — shows the full UI flow.

### Real evaluation against local Ollama
- Target URL: `http://localhost:11434`
- Target Type: `ollama`
- Model: `llama3.1:8b` (or any model you have pulled)

### Real evaluation against Groq / OpenAI-compatible API
- Target URL: `https://api.groq.com/openai/v1/chat/completions`
- Target Type: `openai`
- Model: `llama-3.1-8b-instant`
- API Key: your `gsk_...` key

---

## API

```bash
# Start evaluation
curl -X POST http://localhost:8000/api/v1/evaluations \
  -H "Content-Type: application/json" \
  -d '{"target_url":"http://localhost:11434","target_type":"ollama","suite":"general_chatbot","depth":"standard","demo":true}'

# List evaluations
curl http://localhost:8000/api/v1/evaluations

# Get report
curl http://localhost:8000/api/v1/evaluations/{eval_id}/report

# Health check
curl http://localhost:8000/health
```

WebSocket stream: `ws://localhost:8000/api/v1/stream/{eval_id}`

---

## Tech Stack

| Layer | Tech | Why |
|-------|------|-----|
| Agent orchestration | **LangGraph** | Conditional routing for adaptive test depth — CrewAI can't do this |
| LLM judge | **Ollama** (Llama 3.1 8B) | Independent from target; local = no cost, no data leakage |
| Backend | **FastAPI** + asyncio | Async I/O for concurrent target calls + WebSocket streaming |
| Event streaming | **Redis** pub/sub | Decouples eval graph from WebSocket consumers; survives reconnects |
| Persistence | **PostgreSQL** + asyncpg | Raw asyncpg (no ORM) — connection pool, JSONB for report blobs |
| Vector store | **ChromaDB** | Test case deduplication across runs — semantic search prevents regenerating identical scenarios |
| Frontend | **React 18** + TypeScript + Vite | Strict TypeScript; `npm run build` passes clean |
| Graph viz | **React Flow** | Live agent graph with active/complete node states |
| Charts | **Recharts** | Radar chart for 5-dimension score breakdown |
| Containers | **Docker** + Compose | `docker compose up` brings up all 4 services |

---

## Agents

| Agent | Role |
|-------|------|
| **Supervisor** | Creates test plan, dispatches agents, re-dispatches with harder tests if pass rate >90% |
| **Scenario Generator** | LLM-generated test cases: happy path, edge cases, adversarial, hallucination traps, out-of-scope |
| **Security Agent** | Hardcoded injection battery (25 patterns): prompt injection, jailbreaks, system prompt extraction |
| **Consistency Agent** | Paraphrase consistency, multi-turn context coherence |
| **Executor** | Async HTTP calls to target API; supports ollama / openai-compatible / simple formats |
| **Evaluator** | LLM-as-judge: accuracy, relevance, hallucination, safety, helpfulness (each 0–1) |
| **Report Generator** | Synthesizes scores → structured report + LLM-written narrative |

---

## Evaluation Scores

Each response is scored on 5 dimensions (0–1):

| Dimension | What it measures |
|-----------|-----------------|
| **Accuracy** | Factual correctness |
| **Relevance** | On-topic, answers the question |
| **Hallucination** | 1.0 = no hallucination detected |
| **Safety** | Harmful / policy-violating content (0 = failed) |
| **Helpfulness** | Practical usefulness of the response |

Pass threshold: overall ≥ 0.6. Security injections that succeed override safety score to 0.

---

## Environment Variables

```bash
# Judge LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Databases
POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/agentprobe
REDIS_URL=redis://localhost:6379
CHROMADB_PATH=./data/chromadb

# Auth (leave empty to disable in dev)
AGENTPROBE_API_KEY=

LOG_LEVEL=INFO
```

---

## Project Structure

```
agentprobe/
├── backend/
│   ├── app/
│   │   ├── agents/          # 7 LangGraph agent nodes + prompts/
│   │   ├── api/             # FastAPI routers (evaluations, stream, health)
│   │   ├── core/            # settings.py, auth.py
│   │   ├── models/          # Pydantic schemas
│   │   ├── services/        # database.py, redis_client.py, chroma_store.py
│   │   └── tools/           # target_caller, scoring, injection_battery
│   ├── db/init.sql          # PostgreSQL schema
│   ├── test_suites/         # YAML test suites (general_chatbot, injection_patterns)
│   └── tests/               # pytest suite
├── frontend/
│   └── src/
│       ├── components/      # AgentGraph, EventFeed, ScoreChart, ScoreGauge, ...
│       └── hooks/           # useEvaluations, useEventStream
├── k8s/                     # Kubernetes manifests
├── docker-compose.yml
└── .env.example
```
