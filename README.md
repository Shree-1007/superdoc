# SuperDocs — Agentic Compliance Engine

> An agentic system that ingests mixed-format documents, extracts facts with source tracing, detects conflicts, checks compliance rules, and produces grounded deliverables — all gated by human review.

**Domain:** Vendor contract compliance (contracts, amendments, invoices)

## Quick Start (Clone to Working in Minutes)

```bash
# 1. Clone the repository
git clone <repo-url> && cd doctask-shreekant

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure your environment variables
# Note: The system requires a valid Gemini API key for production mode
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_key_here

# 4. Start the backend server
python -m uvicorn backend.main:app --reload

# 5. Start the React frontend (in a new terminal)
cd superdocs-frontend 
npm install 
npm run dev

# 6. Open your browser to http://localhost:5173
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
│  LangGraph Orchestration │ AsyncSqliteSaver Checkpointer         │
└─────────────────────────────────────────────────────────────────┘
         │
    ┌────▼─────┐    ┌──────────────┐
    │  rules/  │    │  documents/  │
    │  *.yaml  │    │  (watched)   │
    └──────────┘    └──────────────┘
```

## How to use the "Simulate Server Crash" Feature

One of the standout features of this system is its extreme resilience to mid-execution failures, utilizing **LangGraph's state persistence** and **Python's `asyncio` task cancellation**.

To test this feature:
1. Start the backend and frontend servers.
2. Open the frontend and upload some documents.
3. Click **"Start Analysis"**.
4. **Immediately** click the red **"✕ Simulate Server Crash"** button while the pipeline is spinning (e.g., during the "Extract Facts" or "Detect Conflicts" stages).
5. The backend process will be instantly cancelled, terminating the active Gemini API call (`gemini-3.6-flash`), and the UI will drop into an Error state.
6. Click **"↻ Resume from Checkpoint"**. The backend will query the SQLite database, reconstitute the exact state graph, and pick up right where it left off, successfully navigating to the Human Review stage without data loss.

## The 10 Required Behaviors

| # | Requirement | Status | How |
|---|---|---|---|
| 1 | Visible steps with branching | ✅ | 7 LangGraph nodes, conditional edges (retry/skip/escalate) |
| 2 | Survives being stopped | ✅ | AsyncSqliteSaver checkpointer and `asyncio` task cancellation |
| 3 | Human holds the gate | ✅ | `interrupt_before=["human_review_gate"]`, item-by-item review |
| 4 | Machine can drive it | ✅ | Full REST API: `/api/run/start`, `/api/run/submit_review/{id}` |
| 5 | Never bluffs | ✅ | Source tracing on every claim, honesty prompts, empty-findings allowed |
| 6 | Stranger can run it | ✅ | Single README, `pip install` + `uvicorn` |
| 7 | Proves itself | ✅ | 10+ pytest tests, all run without API keys (`MOCK_LLM=true`) |
| 8 | Prompt injection defense | ✅ | `sanitize_input` node with regex detection, flagged not followed |
| 9 | Concurrent runs | ✅ | Thread-isolated state, tested in `test_concurrent.py` |
| 10 | Cost tracking | ✅ | Per-stage `StageLog` with timing, `/api/run/cost/{id}` endpoint |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/run/start` | Start a pipeline run |
| `GET` | `/api/run/state/{thread_id}` | Get current run state |
| `POST` | `/api/run/submit_review/{thread_id}` | Submit human review decisions |
| `POST` | `/api/run/kill/{thread_id}` | Simulate server crash / instant cancel |
| `POST` | `/api/run/resume/{thread_id}` | Resume from checkpoint |
| `GET` | `/api/run/cost/{thread_id}` | Get cost/timing report |

## Configuration Over Code

Compliance rules live in `rules/*.yaml`. Adding a new rule is a YAML edit:

```yaml
- name: "New Fee Cap"
  type: monetary_cap
  cap: 60000
  severity: high
```

No code changes needed. Restart picks up new rules automatically.

## Engineering Design Decisions

1. **AsyncSqliteSaver Checkpointer**: LangGraph's checkpointer is used for state persistence. If the process is killed midway, it can seamlessly resume from the last known checkpoint using the same thread ID.
2. **Asynchronous LLM API Calls**: Upgraded to use `gemini-3.6-flash` via `await model.generate_content_async()`. By using purely async endpoints, the FastAPI event loop remains unblocked, allowing instant interception of the `/kill` command even when waiting on Google's servers.
3. **Task Cancellation**: Implemented `asyncio.Task.cancel()` to provide a true, immediate server crash simulation rather than just setting a boolean flag between graph states.
4. **Graceful LLM Fallback (MOCK_LLM)**: By setting `MOCK_LLM=false` and providing a Gemini API key, the system does real extraction. If the API fails or `MOCK_LLM=true` is set, it seamlessly falls back to local regex extraction.
5. **Injection detection before ingestion**: The `sanitize_input` node runs first, flags patterns, but never blocks processing — injections are data, not commands.

## Known Limitations

- **Single-process Checkpointing limits**: While SqliteSaver is great for this scale, horizontally scaling this would require switching to PostgresCheckpointer (available in LangGraph).
- **No watched-folder daemon**: The `documents/` folder is read on-demand during pipeline execution, not continuously monitored via a file-system watcher daemon.
