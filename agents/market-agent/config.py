"""
Hyper-Sentinel v3 — MarketAgent Configuration
==============================================
Centralized, environment-driven configuration.
All config flows from env vars — no hardcoded values.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


# ─── NATS Subjects ──────────────────────────────────────────────
SUBJECT_MARKET_DATA = "sentinel.market.data"
SUBJECT_RISK_INPUT = "sentinel.risk.input"
SUBJECT_GOVERNANCE_AUDIT = "sentinel.governance.audit"

# JetStream stream/consumer names
STREAM_NAME = "SENTINEL_STREAM"
CONSUMER_NAME = "MARKET_AGENT_CONSUMER"

# ─── LLM Provider Mapping ──────────────────────────────────────
PROVIDER_MODEL_MAP: dict[str, str] = {
    "CLAUDE": "anthropic/claude-sonnet-4-5",
    "GEMINI": "google/gemini-2.0-flash",
    "GROK": "xai/grok-2",
    "OLLAMA": "ollama/deepseek-r1:1.5b",
}

# ─── Default Watchlist ──────────────────────────────────────────
DEFAULT_SYMBOLS = ["SPY", "QQQ", "BTC-USD"]


@dataclass(frozen=True)
class AgentConfig:
    """Immutable agent configuration loaded once at startup."""

    # Agent identity
    agent_name: str = field(
        default_factory=lambda: os.getenv("AGENT_NAME", "MarketAgent")
    )

    # NATS
    nats_url: str = field(
        default_factory=lambda: os.getenv("NATS_URL", "nats://localhost:4222")
    )

    # LLM
    llm_provider: str = field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "CLAUDE").upper()
    )
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", ""))
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))

    # Database
    db_path: str = field(
        default_factory=lambda: os.getenv("DB_PATH", "data/agent_decisions.db")
    )

    # Logging
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper()
    )

    @property
    def resolved_model(self) -> str:
        """Resolve the Upsonic model string from provider + optional override."""
        if self.llm_model:
            return self.llm_model
        return PROVIDER_MODEL_MAP.get(self.llm_provider, PROVIDER_MODEL_MAP["CLAUDE"])

    def __post_init__(self) -> None:
        if self.llm_provider not in PROVIDER_MODEL_MAP:
            raise ValueError(
                f"Unknown LLM_PROVIDER '{self.llm_provider}'. "
                f"Valid options: {list(PROVIDER_MODEL_MAP.keys())}"
            )

        # Bridge LLM_API_KEY → provider-specific env var that Upsonic expects
        if self.llm_api_key:
            provider_env_map = {
                "CLAUDE": "ANTHROPIC_API_KEY",
                "GEMINI": "GOOGLE_API_KEY",
                "GROK": "XAI_API_KEY",
            }
            env_var = provider_env_map.get(self.llm_provider)
            if env_var and not os.getenv(env_var):
                os.environ[env_var] = self.llm_api_key
