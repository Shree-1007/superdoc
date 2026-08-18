"""Application configuration via pydantic-settings. Reads from .env file."""
import os
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # LLM mode
    mock_llm: bool = True

    # Logging
    log_level: str = "INFO"

    # Directories
    watched_dir: str = "./documents"
    rules_dir: str = "./rules"

    # Checkpoint persistence
    checkpoint_db: str = "./checkpoints/agent_state.db"

    # Optional LLM keys
    openai_api_key: str = ""
    google_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Ensure required directories exist
for d in [settings.watched_dir, settings.rules_dir, os.path.dirname(settings.checkpoint_db)]:
    Path(d).mkdir(parents=True, exist_ok=True)
