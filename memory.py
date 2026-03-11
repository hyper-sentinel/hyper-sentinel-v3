"""
Sentinel Memory — Persistent state layer for autonomous operation.

Stores decisions, portfolio snapshots, and agent memory.
Uses JSON files locally, upgrades to Postgres when DATABASE_URL is set.

The memory module gives Sentinel the ability to:
  • Remember what it's seen and done across restarts
  • Track portfolio equity over time
  • Replay decision history for analysis
  • Avoid repeating actions (deduplication)
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("sentinel.memory")

# ── Try Postgres, fall back to JSON files ────────────────────────────
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class MemoryStore:
    """
    Persistent memory for Sentinel.

    Stores to local JSON files by default.
    Connects to Postgres when DATABASE_URL is set.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.db_url = os.getenv("DATABASE_URL", "").strip()
        self.use_postgres = bool(self.db_url) and POSTGRES_AVAILABLE
        self._conn = None

        if self.use_postgres:
            self._init_postgres()
        else:
            self._init_local()

    # ── Postgres Backend ─────────────────────────────────────────────

    def _init_postgres(self):
        """Initialize Postgres tables."""
        try:
            self._conn = psycopg2.connect(self.db_url)
            self._conn.autocommit = True
            with self._conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS decisions (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        monitor VARCHAR(50),
                        alert_title TEXT,
                        action VARCHAR(50),
                        result TEXT,
                        auto_executed BOOLEAN DEFAULT FALSE,
                        data JSONB
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        total_equity NUMERIC,
                        positions JSONB,
                        pnl_24h NUMERIC,
                        data JSONB
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS agent_memory (
                        key VARCHAR(255) PRIMARY KEY,
                        value JSONB,
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS trade_log (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        venue VARCHAR(50),
                        symbol VARCHAR(20),
                        side VARCHAR(10),
                        size NUMERIC,
                        price NUMERIC,
                        pnl NUMERIC,
                        data JSONB
                    );
                """)
            logger.info("Postgres memory initialized (4 tables)")
        except Exception as e:
            logger.error(f"Postgres init failed: {e} — falling back to local")
            self.use_postgres = False
            self._init_local()

    # ── Local JSON Backend ───────────────────────────────────────────

    def _init_local(self):
        """Initialize local JSON file storage."""
        (self.data_dir / "decisions").mkdir(exist_ok=True)
        (self.data_dir / "snapshots").mkdir(exist_ok=True)
        (self.data_dir / "memory").mkdir(exist_ok=True)
        (self.data_dir / "trades").mkdir(exist_ok=True)
        logger.info(f"Local memory initialized at {self.data_dir}/")

    # ── Decision Logging ─────────────────────────────────────────────

    def log_decision(
        self,
        monitor: str,
        alert_title: str,
        action: str,
        result: str,
        auto_executed: bool = False,
        data: dict | None = None,
    ):
        """Log a sentinel decision."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "monitor": monitor,
            "alert_title": alert_title,
            "action": action,
            "result": result,
            "auto_executed": auto_executed,
            "data": data or {},
        }

        if self.use_postgres:
            try:
                with self._conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO decisions 
                           (monitor, alert_title, action, result, auto_executed, data)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (monitor, alert_title, action, result, auto_executed,
                         json.dumps(data or {})),
                    )
            except Exception as e:
                logger.error(f"Postgres decision log failed: {e}")
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.data_dir / "decisions" / f"{today}.jsonl"
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        logger.info(f"Decision: {action} — {alert_title}")

    def get_decisions(self, days: int = 7, limit: int = 50) -> list[dict]:
        """Get recent decisions."""
        if self.use_postgres:
            try:
                with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT * FROM decisions 
                           WHERE timestamp > NOW() - INTERVAL '%s days'
                           ORDER BY timestamp DESC LIMIT %s""",
                        (days, limit),
                    )
                    return [dict(r) for r in cur.fetchall()]
            except Exception as e:
                logger.error(f"Postgres query failed: {e}")
                return []
        else:
            decisions = []
            dec_dir = self.data_dir / "decisions"
            for f in sorted(dec_dir.glob("*.jsonl"), reverse=True)[:days]:
                with open(f) as fh:
                    for line in fh:
                        decisions.append(json.loads(line))
            return decisions[:limit]

    # ── Portfolio Snapshots ──────────────────────────────────────────

    def save_snapshot(
        self,
        total_equity: float,
        positions: list[dict],
        pnl_24h: float = 0,
        data: dict | None = None,
    ):
        """Save a portfolio snapshot."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "total_equity": total_equity,
            "positions": positions,
            "pnl_24h": pnl_24h,
            "data": data or {},
        }

        if self.use_postgres:
            try:
                with self._conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO portfolio_snapshots 
                           (total_equity, positions, pnl_24h, data)
                           VALUES (%s, %s, %s, %s)""",
                        (total_equity, json.dumps(positions), pnl_24h,
                         json.dumps(data or {})),
                    )
            except Exception as e:
                logger.error(f"Postgres snapshot failed: {e}")
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            snap_file = self.data_dir / "snapshots" / f"{today}.jsonl"
            with open(snap_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        logger.info(f"Snapshot: equity=${total_equity:,.2f}, PnL=${pnl_24h:+,.2f}")

    def get_equity_curve(self, days: int = 30) -> list[dict]:
        """Get equity snapshots for charting."""
        if self.use_postgres:
            try:
                with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        """SELECT timestamp, total_equity, pnl_24h 
                           FROM portfolio_snapshots
                           WHERE timestamp > NOW() - INTERVAL '%s days'
                           ORDER BY timestamp ASC""",
                        (days,),
                    )
                    return [dict(r) for r in cur.fetchall()]
            except Exception as e:
                logger.error(f"Postgres query failed: {e}")
                return []
        else:
            snapshots = []
            snap_dir = self.data_dir / "snapshots"
            for f in sorted(snap_dir.glob("*.jsonl"))[-days:]:
                with open(f) as fh:
                    for line in fh:
                        entry = json.loads(line)
                        snapshots.append({
                            "timestamp": entry["timestamp"],
                            "total_equity": entry["total_equity"],
                            "pnl_24h": entry.get("pnl_24h", 0),
                        })
            return snapshots

    # ── Trade Log ────────────────────────────────────────────────────

    def log_trade(
        self,
        venue: str,
        symbol: str,
        side: str,
        size: float,
        price: float,
        pnl: float = 0,
        data: dict | None = None,
    ):
        """Log a completed trade."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "venue": venue,
            "symbol": symbol,
            "side": side,
            "size": size,
            "price": price,
            "pnl": pnl,
            "data": data or {},
        }

        if self.use_postgres:
            try:
                with self._conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO trade_log 
                           (venue, symbol, side, size, price, pnl, data)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (venue, symbol, side, size, price, pnl,
                         json.dumps(data or {})),
                    )
            except Exception as e:
                logger.error(f"Postgres trade log failed: {e}")
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            trade_file = self.data_dir / "trades" / f"{today}.jsonl"
            with open(trade_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        logger.info(f"Trade: {side} {size} {symbol} @ ${price:,.2f} on {venue}")

    # ── Key-Value Memory (agent remembers things) ────────────────────

    def remember(self, key: str, value) -> None:
        """Store a value in persistent memory."""
        if self.use_postgres:
            try:
                with self._conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO agent_memory (key, value, updated_at)
                           VALUES (%s, %s, NOW())
                           ON CONFLICT (key) DO UPDATE
                           SET value = EXCLUDED.value, updated_at = NOW()""",
                        (key, json.dumps(value)),
                    )
            except Exception as e:
                logger.error(f"Postgres remember failed: {e}")
        else:
            mem_file = self.data_dir / "memory" / "store.json"
            store = {}
            if mem_file.exists():
                store = json.loads(mem_file.read_text())
            store[key] = {"value": value, "updated_at": datetime.now().isoformat()}
            mem_file.write_text(json.dumps(store, indent=2))

    def recall(self, key: str, default=None):
        """Retrieve a value from persistent memory."""
        if self.use_postgres:
            try:
                with self._conn.cursor() as cur:
                    cur.execute(
                        "SELECT value FROM agent_memory WHERE key = %s", (key,)
                    )
                    row = cur.fetchone()
                    return json.loads(row[0]) if row else default
            except Exception as e:
                logger.error(f"Postgres recall failed: {e}")
                return default
        else:
            mem_file = self.data_dir / "memory" / "store.json"
            if not mem_file.exists():
                return default
            store = json.loads(mem_file.read_text())
            entry = store.get(key)
            return entry["value"] if entry else default

    def forget(self, key: str) -> bool:
        """Remove a value from persistent memory."""
        if self.use_postgres:
            try:
                with self._conn.cursor() as cur:
                    cur.execute("DELETE FROM agent_memory WHERE key = %s", (key,))
                    return cur.rowcount > 0
            except Exception as e:
                logger.error(f"Postgres forget failed: {e}")
                return False
        else:
            mem_file = self.data_dir / "memory" / "store.json"
            if not mem_file.exists():
                return False
            store = json.loads(mem_file.read_text())
            if key in store:
                del store[key]
                mem_file.write_text(json.dumps(store, indent=2))
                return True
            return False

    # ── Stats ────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get memory store statistics."""
        if self.use_postgres:
            try:
                with self._conn.cursor() as cur:
                    stats = {}
                    for table in ["decisions", "portfolio_snapshots", "trade_log", "agent_memory"]:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        stats[table] = cur.fetchone()[0]
                    return {"backend": "postgres", **stats}
            except Exception as e:
                return {"backend": "postgres", "error": str(e)}
        else:
            return {
                "backend": "local_json",
                "decisions": len(list((self.data_dir / "decisions").glob("*.jsonl"))),
                "snapshots": len(list((self.data_dir / "snapshots").glob("*.jsonl"))),
                "trades": len(list((self.data_dir / "trades").glob("*.jsonl"))),
                "memory_keys": len(self._get_local_keys()),
            }

    def _get_local_keys(self) -> list[str]:
        mem_file = self.data_dir / "memory" / "store.json"
        if not mem_file.exists():
            return []
        return list(json.loads(mem_file.read_text()).keys())
