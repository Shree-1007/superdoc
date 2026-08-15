# SuperDocs — Agentic Compliance Engine

> An agentic system that ingests mixed-format documents, extracts facts with source tracing, detects conflicts, checks compliance rules, and produces grounded deliverables — all gated by human review.

**Domain:** Vendor contract compliance (contracts, amendments, invoices)

## Quick Start (Clone to Working in Minutes)

```bash
# 1. Clone and enter
git clone <repo-url> && cd doctask-shreekant

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Copy environment config
cp .env.example .env

# 4. Start the backend
uvicorn backend.main:app --reload

# 5. Start the frontend (in another terminal)
cd superdocs-frontend && npm install && npm run dev

# 6. Open http://localhost:5173
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Frontend (:5173)                      │
│   Pipeline Viz │ Finding Cards │ Approve/Reject │ Cost Report   │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────────┐
│                  FastAPI Backend (:8000)                         │
│                                                                  │
│  ┌──────────┐   ┌────────┐   ┌──────────┐   ┌────────────────┐ │
│  │ Sanitize │──▶│ Ingest │──▶│ Extract  │──▶│  Detect        │ │
│  │  Input   │   │  Docs  │   │  Facts   │   │  Conflicts     │ │
│  └──────────┘   └────────┘   └──────────┘   └───────┬────────┘ │
│                                                      │          │
│  ┌──────────┐   ┌────────────────┐   ┌───────────────▼────────┐│
│  │ Generate │◀──│ Human Review   │◀──│   Check Rules          ││
│  │Deliverble│   │ Gate (HITL)    │   │   (YAML config)        ││
│  └──────────┘   └────────────────┘   └────────────────────────┘│
│                                                                  │
│  LangGraph Orchestration │ MemorySaver Checkpointer             │
└─────────────────────────────────────────────────────────────────┘
         │
    ┌────▼─────┐    ┌──────────────┐
    │  rules/  │    │  documents/  │
    │  *.yaml  │    │  (watched)   │
    └──────────┘    └──────────────┘
```

## The 10 Required Behaviors

| # | Requirement | Status | How |
|---|---|---|---|
| 1 | Visible steps with branching | ✅ | 7 LangGraph nodes, conditional edges (retry/skip/escalate) |
| 2 | Survives being stopped | ✅ | MemorySaver checkpointer, tested in `test_resume.py` |
| 3 | Human holds the gate | ✅ | `interrupt_before=["human_review_gate"]`, item-by-item review |
| 4 | Machine can drive it | ✅ | Full REST API: `/api/run/start`, `/api/run/submit_review/{id}` |
| 5 | Never bluffs | ✅ | Source tracing on every claim, honesty prompts, empty-findings allowed |
| 6 | Stranger can run it | ✅ | Single README, `pip install` + `uvicorn` |
| 7 | Proves itself | ✅ | 10+ pytest tests, all run without API keys (`MOCK_LLM=true`) |
| 8 | Prompt injection defense | ✅ | `sanitize_input` node with regex detection, flagged not followed |
| 9 | Concurrent runs | ✅ | Thread-isolated state, tested in `test_concurrent.py` |
| 10 | Cost tracking | ✅ | Per-stage `StageLog` with timing, `/api/run/cost/{id}` endpoint |

## Run Tests (No API Key Needed)

```bash
pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/run/start` | Start a pipeline run |
| `GET` | `/api/run/state/{thread_id}` | Get current run state |
| `POST` | `/api/run/submit_review/{thread_id}` | Submit human review decisions |
| `GET` | `/api/run/cost/{thread_id}` | Get cost/timing report |
| `POST` | `/api/documents/upload` | Upload documents |

## Configuration Over Code

Compliance rules live in `rules/*.yaml`. Adding a new rule is a YAML edit:

```yaml
- name: "New Fee Cap"
  type: monetary_cap
  cap: 60000
  severity: high
```

No code changes needed. Restart picks up new rules automatically.

## Design Decisions

1. **SqliteSaver Checkpointer**: LangGraph's `SqliteSaver` is used for state persistence. If the process is killed midway, it can seamlessly resume from the last known checkpoint using the same thread ID.
2. **Graceful LLM Fallback (MOCK_LLM)**: By setting `MOCK_LLM=false` and providing a Gemini API key, the system does real extraction via Gemini Flash. If the API fails or `MOCK_LLM=true` is set (e.g. for deterministic unit testing), it seamlessly falls back to local regex extraction.
3. **Injection detection before ingestion**: The `sanitize_input` node runs first, flags patterns, but never blocks processing — injections are data, not commands.
4. **Branching on check_rules**: Retry up to 3x on failure, skip review if no findings found, escalate to human if retries exhausted.

## Known Limitations (Honest)

- **Single-process Checkpointing limits**: While SqliteSaver is great for this scale, horizontally scaling this would require switching to PostgresCheckpointer (available in LangGraph).
- **No watched-folder daemon**: The `documents/` folder is read on-demand during pipeline execution, not continuously monitored via a file-system watcher daemon (like watchdog).

## File Structure

```
doctask-shreekant/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py             # pydantic-settings (.env)
│   ├── models.py             # API request/response schemas
│   ├── agent/
│   │   ├── state.py          # AgentState TypedDict
│   │   ├── nodes.py          # All graph node functions
│   │   ├── graph.py          # Graph construction
│   │   └── prompts.py        # System prompts (honesty, injection defense)
│   ├── api/
│   │   └── routes.py         # All REST endpoints
│   └── services/
│       ├── document_parser.py # PDF/DOCX/TXT parsing
│       └── rule_engine.py    # YAML-based compliance rules
├── rules/
│   └── contract_playbook.yaml # Compliance rules (config, not code)
├── documents/                 # Upload/watched folder
├── tests/
│   ├── test_resume.py         # Kill & resume
│   ├── test_concurrent.py     # Concurrent runs
│   ├── test_injection.py      # Prompt injection defense
│   ├── test_human_gate.py     # Item-by-item review
│   └── test_cost_tracking.py  # Per-stage timing
├── superdocs-frontend/        # React + Vite + Tailwind
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```
