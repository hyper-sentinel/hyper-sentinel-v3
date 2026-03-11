"""
Hyper-Sentinel v2 — MarketAgent NATS Subscriber
=================================================
The main entry point. Subscribes to sentinel.market.data via NATS JetStream,
dispatches to the Upsonic MarketAgent, publishes results to sentinel.risk.input,
and logs every decision to SQLite.

Pattern: tobalo/agentic-osint/swarm.py (async NATS subscriber loop)
Messaging: All inter-agent communication via NATS — no direct function calls.
Logging: Every decision → SQLite (immutable audit trail)
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone

import nats
from nats.js.api import StreamConfig, ConsumerConfig, RetentionPolicy, AckPolicy

from agent import analyze_market
from config import (
    AgentConfig,
    STREAM_NAME,
    CONSUMER_NAME,
    SUBJECT_MARKET_DATA,
    SUBJECT_RISK_INPUT,
    SUBJECT_GOVERNANCE_AUDIT,
)
from db import DecisionLogger
from models import MarketDataRequest, AgentDecision, DecisionStatus

# ─── Logging Setup ──────────────────────────────────────────────

config = AgentConfig()

logging.basicConfig(
    level=getattr(logging, config.log_level, logging.INFO),
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentinel.market-agent")


# ─── Banner ─────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██╗  ██╗██╗   ██╗██████╗ ███████╗██████╗                  ║
║   ██║  ██║╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗                 ║
║   ███████║ ╚████╔╝ ██████╔╝█████╗  ██████╔╝                 ║
║   ██╔══██║  ╚██╔╝  ██╔═══╝ ██╔══╝  ██╔══██╗                 ║
║   ██║  ██║   ██║   ██║     ███████╗██║  ██║                  ║
║   ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝                ║
║                                                              ║
║   S E N T I N E L   v 2  —  M A R K E T   A G E N T         ║
║   Built like NASA would.                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


async def _ensure_stream(js) -> None:
    """
    Create the JetStream stream if it doesn't exist.
    This stream captures ALL sentinel.* subjects for durability.
    """
    try:
        await js.find_stream_name_by_subject(SUBJECT_MARKET_DATA)
        logger.info(f"JetStream stream found for {SUBJECT_MARKET_DATA}")
    except Exception:
        logger.info(f"Creating JetStream stream: {STREAM_NAME}")
        await js.add_stream(
            StreamConfig(
                name=STREAM_NAME,
                subjects=["sentinel.>"],
                retention=RetentionPolicy.LIMITS,
                max_msgs=100_000,
                max_bytes=256 * 1024 * 1024,  # 256MB
                max_age=7 * 24 * 60 * 60,  # 7 days in seconds
                storage="file",
                num_replicas=1,
            )
        )
        logger.info(f"Stream {STREAM_NAME} created with subjects: sentinel.>")


async def _process_message(
    msg,
    nc,
    js,
    decision_logger: DecisionLogger,
    agent_config: AgentConfig,
) -> None:
    """
    Process a single NATS message through the full MarketAgent pipeline.

    Flow:
        1. Deserialize the message
        2. Run the Upsonic MarketAgent
        3. Publish output to sentinel.risk.input
        4. Publish audit record to sentinel.governance.audit
        5. Log decision to SQLite
        6. Acknowledge the message (JetStream)
    """
    start_time = time.monotonic()
    request_data = msg.data.decode()

    logger.info(f"← Received on {msg.subject}: {request_data[:200]}...")

    try:
        # 1. Deserialize
        raw = json.loads(request_data)
        request = MarketDataRequest(**raw)

        # 2. Run the MarketAgent
        analysis = await analyze_market(request, agent_config)

        # 3. Publish to sentinel.risk.input (next agent in chain)
        output_json = analysis.model_dump_json()
        await nc.publish(SUBJECT_RISK_INPUT, output_json.encode())
        logger.info(f"→ Published to {SUBJECT_RISK_INPUT}: risk={analysis.risk_level.value}")

        # 4. Publish audit record to governance
        audit_record = {
            "agent": agent_config.agent_name,
            "request_id": request.request_id,
            "action": "market_analysis",
            "risk_level": analysis.risk_level.value,
            "anomalies_count": len(analysis.anomalies),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await nc.publish(
            SUBJECT_GOVERNANCE_AUDIT, json.dumps(audit_record).encode()
        )

        # 5. Log to SQLite
        latency_ms = int((time.monotonic() - start_time) * 1000)
        decision = AgentDecision(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_name=agent_config.agent_name,
            subject=msg.subject,
            input_data=request_data,
            output_data=output_json,
            decision=f"risk={analysis.risk_level.value}, anomalies={len(analysis.anomalies)}",
            confidence=analysis.confidence,
            provider=agent_config.llm_provider,
            model=agent_config.resolved_model,
            latency_ms=latency_ms,
            status=DecisionStatus.COMPLETED,
        )
        row_id = decision_logger.log(decision)

        logger.info(
            f"✓ Decision #{row_id} logged | "
            f"latency={latency_ms}ms | "
            f"provider={agent_config.llm_provider}"
        )

    except Exception as e:
        # Fail-secure: log the failure, never silently pass through
        latency_ms = int((time.monotonic() - start_time) * 1000)
        logger.error(f"✗ Processing failed: {e}", exc_info=True)

        decision = AgentDecision(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_name=agent_config.agent_name,
            subject=msg.subject,
            input_data=request_data,
            output_data=None,
            decision="FAILED — action blocked (fail-secure)",
            confidence=0.0,
            provider=agent_config.llm_provider,
            model=agent_config.resolved_model,
            latency_ms=latency_ms,
            status=DecisionStatus.FAILED,
            error=str(e),
        )
        decision_logger.log(decision)

    finally:
        # 6. Acknowledge the JetStream message
        try:
            await msg.ack()
        except Exception:
            pass  # Best effort ack — JetStream will redeliver if needed


async def main() -> None:
    """
    Main entry point — connect to NATS, subscribe, process forever.
    Follows the agentic-osint/swarm.py pattern with JetStream durability.
    """
    print(BANNER)

    agent_config = AgentConfig()
    decision_logger = DecisionLogger(agent_config.db_path)

    logger.info(f"Agent:    {agent_config.agent_name}")
    logger.info(f"NATS:     {agent_config.nats_url}")
    logger.info(f"Provider: {agent_config.llm_provider}")
    logger.info(f"Model:    {agent_config.resolved_model}")
    logger.info(f"DB:       {agent_config.db_path}")

    # Connect to NATS
    nc = await nats.connect(
        agent_config.nats_url,
        name=agent_config.agent_name,
        max_reconnect_attempts=60,
        reconnect_time_wait=2,
    )
    logger.info(f"NATS connected: {nc.connected_url}")

    # Get JetStream context
    js = nc.jetstream()

    # Ensure our stream exists
    await _ensure_stream(js)

    # Subscribe via JetStream push subscription with callback
    # (matches agentic-osint/swarm.py pattern)
    async def message_handler(msg):
        await _process_message(msg, nc, js, decision_logger, agent_config)

    # Delete stale consumer if it exists from a previous session
    try:
        await js.delete_consumer(STREAM_NAME, CONSUMER_NAME)
        logger.info(f"Cleared stale consumer: {CONSUMER_NAME}")
    except Exception:
        pass  # Consumer doesn't exist yet — that's fine

    sub = await js.subscribe(
        SUBJECT_MARKET_DATA,
        durable=CONSUMER_NAME,
        stream=STREAM_NAME,
        cb=message_handler,
    )
    logger.info(f"Subscribed to {SUBJECT_MARKET_DATA} (durable: {CONSUMER_NAME})")

    # Graceful shutdown handler
    shutdown_event = asyncio.Event()

    def _signal_handler():
        logger.info("Shutdown signal received — draining...")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    logger.info("MarketAgent is ONLINE — awaiting messages...")
    logger.info(f"Total decisions logged: {decision_logger.count()}")

    # Wait until shutdown signal
    await shutdown_event.wait()

    # Cleanup
    logger.info("Draining NATS connection...")
    await sub.unsubscribe()
    await nc.drain()
    logger.info("MarketAgent shut down cleanly.")


if __name__ == "__main__":
    asyncio.run(main())

