"""
Hyper-Sentinel — SQLite Decision Logger
===========================================
Every agent decision is logged with full context.
Schema mirrors gogent's agent_logs but extended for financial intelligence.
"""

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

from models import AgentDecision

logger = logging.getLogger(__name__)

# ─── Schema ─────────────────────────────────────────────────────

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS agent_decisions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    NOT NULL,
    agent_name      TEXT    NOT NULL,
    subject         TEXT    NOT NULL,
    input_data      TEXT    NOT NULL,
    output_data     TEXT,
    decision        TEXT,
    confidence      REAL,
    provider        TEXT    NOT NULL,
    model           TEXT    NOT NULL,
    latency_ms      INTEGER,
    status          TEXT    DEFAULT 'completed',
    error           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_agent_decisions_timestamp ON agent_decisions(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_agent ON agent_decisions(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_status ON agent_decisions(status);
"""

INSERT_SQL = """
INSERT INTO agent_decisions (
    timestamp, agent_name, subject, input_data, output_data,
    decision, confidence, provider, model, latency_ms, status, error
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


class DecisionLogger:
    """
    Thread-safe SQLite logger for agent decisions.

    Usage:
        logger = DecisionLogger("data/agent_decisions.db")
        logger.log(decision)
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._ensure_directory()
        self._init_schema()
        logger.info(f"DecisionLogger initialized → {self.db_path}")

    def _ensure_directory(self) -> None:
        """Create the data directory if it doesn't exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context-managed SQLite connection with WAL mode for concurrency."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._connection() as conn:
            conn.executescript(CREATE_TABLE_SQL + CREATE_INDEX_SQL)

    def log(self, decision: AgentDecision) -> int:
        """
        Log an agent decision. Returns the row ID.

        Every call to this method creates an immutable audit record.
        Nothing is ever deleted — this is the ground truth.
        """
        with self._connection() as conn:
            cursor = conn.execute(
                INSERT_SQL,
                (
                    decision.timestamp,
                    decision.agent_name,
                    decision.subject,
                    decision.input_data,
                    decision.output_data,
                    decision.decision,
                    decision.confidence,
                    decision.provider,
                    decision.model,
                    decision.latency_ms,
                    decision.status.value,
                    decision.error,
                ),
            )
            row_id = cursor.lastrowid
            logger.debug(f"Logged decision #{row_id} for {decision.agent_name}")
            return row_id

    def get_recent(self, limit: int = 10) -> list[dict]:
        """Retrieve the most recent decisions (for debugging/monitoring)."""
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM agent_decisions ORDER BY id DESC LIMIT ?;",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def count(self) -> int:
        """Total number of logged decisions."""
        with self._connection() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM agent_decisions;"
            ).fetchone()[0]
