"""
memory_config.py — Persistent memory for Agno agents.

Provides:
  1. Session DB — conversation history persists across restarts
  2. Memory Manager — agent learns user facts/preferences over time

Auto-detects backend:
  - DATABASE_URL set → Postgres (production)
  - DATABASE_URL empty → SQLite in data/ (local dev)

Usage in agent.py:
    from memory_config import get_db, get_memory_manager

    db = get_db()                      # session storage
    mm = get_memory_manager()          # user fact memory

Usage in swarm.py (Agno Agent):
    from memory_config import get_db, get_memory_manager

    agent = Agent(
        model=Claude(...),
        db=get_db(),
        memory=get_memory_manager(),
        ...
    )
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger("memory_config")

# ── Detect backend ───────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_POSTGRES = bool(DATABASE_URL)

# ── SQLite fallback path ────────────────────────────────────
SQLITE_FILE = str(Path(__file__).resolve().parent / "data" / "agent.db")
Path(SQLITE_FILE).parent.mkdir(exist_ok=True)


def get_db(
    session_table: str = "agent_sessions",
    memory_table: str = "user_memories",
):
    """
    Create an Agno DB instance for session persistence + memory storage.

    Returns PostgresDb if DATABASE_URL is set, otherwise SqliteDb.
    """
    if USE_POSTGRES:
        from agno.db.postgres import PostgresDb

        db = PostgresDb(
            db_url=DATABASE_URL,
            session_table=session_table,
            memory_table=memory_table,
        )
        logger.info(f"Memory: Postgres ({DATABASE_URL[:30]}...)")
    else:
        from agno.db.sqlite import SqliteDb

        db = SqliteDb(
            db_file=SQLITE_FILE,
            session_table=session_table,
            memory_table=memory_table,
        )
        logger.info(f"Memory: SQLite ({SQLITE_FILE})")

    return db


def get_memory_manager(model=None):
    """
    Create an Agno MemoryManager for learning user facts/preferences.

    Uses a cheap model for memory operations (summarizing, extracting facts).
    Falls back to the user's configured LLM provider.
    """
    from agno.memory.manager import MemoryManager

    db = get_db(memory_table="user_memories")

    if model is None:
        # Pick a cheap model for memory ops
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

        if anthropic_key and anthropic_key != "your-api-key-here":
            from agno.models.anthropic import Claude
            model = Claude(id="claude-haiku-3-20250414", api_key=anthropic_key)
        elif openai_key and openai_key != "your-api-key-here":
            from agno.models.openai import OpenAIChat
            model = OpenAIChat(id="gpt-4o-mini", api_key=openai_key)
        elif gemini_key and gemini_key != "your-api-key-here":
            from agno.models.openai import OpenAIChat
            model = OpenAIChat(
                id="gemini-2.0-flash",
                api_key=gemini_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
        else:
            logger.warning("No API key found for memory manager — memory disabled")
            return None

    mm = MemoryManager(
        model=model,
        db=db,
        update_memories=True,
        add_memories=True,
    )
    logger.info("MemoryManager initialized")
    return mm
