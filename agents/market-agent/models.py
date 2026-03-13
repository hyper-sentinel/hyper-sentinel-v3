"""
Hyper-Sentinel — MarketAgent Data Models
============================================
Pydantic models for structured data flowing through NATS subjects.
Every message is typed, validated, and serializable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RequestType(str, Enum):
    """Types of market data requests the MarketAgent handles."""
    MARKET_SCAN = "market_scan"
    ANOMALY_DETECTION = "anomaly_detection"
    DEEP_ANALYSIS = "deep_analysis"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionStatus(str, Enum):
    """Status of an agent decision."""
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


# ─── Inbound: sentinel.market.data ─────────────────────────────

class MarketDataRequest(BaseModel):
    """Message received on sentinel.market.data."""
    request_id: str
    request_type: RequestType = RequestType.MARKET_SCAN
    symbols: list[str] = Field(default_factory=lambda: ["SPY", "QQQ", "BTC-USD"])
    timeframe: str = "1d"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── Outbound: sentinel.risk.input ─────────────────────────────

class Anomaly(BaseModel):
    """A detected market anomaly."""
    symbol: str
    description: str
    severity: RiskLevel = RiskLevel.MEDIUM
    metric: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None


class MarketAnalysis(BaseModel):
    """Analysis output published to sentinel.risk.input."""
    request_id: str
    agent_name: str = "MarketAgent"
    analysis: str
    anomalies: list[Anomaly] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    symbols_analyzed: list[str] = Field(default_factory=list)
    provider: str = ""
    model: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── SQLite Audit Record ───────────────────────────────────────

class AgentDecision(BaseModel):
    """Full audit record logged to SQLite for every agent action."""
    timestamp: str
    agent_name: str
    subject: str
    input_data: str
    output_data: Optional[str] = None
    decision: Optional[str] = None
    confidence: Optional[float] = None
    provider: str
    model: str
    latency_ms: Optional[int] = None
    status: DecisionStatus = DecisionStatus.COMPLETED
    error: Optional[str] = None
