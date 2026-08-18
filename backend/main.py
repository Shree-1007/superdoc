"""FastAPI application entry point — assembles all components."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.agent.graph import build_graph
from backend.api.routes import router, set_graph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Startup
    logger.info("Building agent graph…")
    async with AsyncSqliteSaver.from_conn_string(settings.checkpoint_db) as checkpointer:
        # Monkeypatch to fix LangGraph/aiosqlite version bug where is_alive doesn't exist
        checkpointer.conn.is_alive = lambda: True
        await checkpointer.setup()
        graph = build_graph(checkpointer=checkpointer)
        set_graph(graph)
        logger.info("Agent graph compiled and ready.")
        logger.info(f"MOCK_LLM={settings.mock_llm}  |  Rules dir={settings.rules_dir}  |  Watched dir={settings.watched_dir}")

        yield

    # Shutdown
    logger.info("Shutting down.")


app = FastAPI(
    title="SuperDocs Agentic Compliance Engine",
    version="1.0.0",
    description=(
        "An agentic system for document analysis, compliance checking, "
        "and human-in-the-loop review. Built for the SuperDocs Task 1 assessment."
    ),
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "SuperDocs Agentic Compliance Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
