"""
Sentinel v2 — Agno Swarm (5-Agent Team)
=========================================
5 specialist agents coordinated by Captain in Agno's coordinate mode.

Usage:
    from swarm import create_swarm, SwarmAgent
    swarm = SwarmAgent()
    response = swarm.chat("What's the BTC outlook?")

Or from the REPL:
    ⚡ You → swarm
    ✓ Swarm active! 5 agents online.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.team import Team

# ── Scrapers ──────────────────────────────────────────────────────

from scrapers.crypto_scraper import get_crypto_price, get_crypto_top_n, search_crypto
from scrapers.fred_scraper import get_fred_series, get_economic_dashboard
from scrapers.y2_scraper import get_news_sentiment, get_news_recap
from scrapers.elfa_scraper import get_trending_tokens, get_social_mentions
from scrapers.x_scraper import XScraper

from scrapers.hyperliquid_scraper import (
    get_hl_config, get_hl_account_info, get_hl_positions,
    get_hl_orderbook, get_hl_open_orders,
)
from scrapers.polymarket_scraper import (
    get_polymarket_markets, search_polymarket, get_polymarket_orderbook,
    get_polymarket_price, buy_polymarket, sell_polymarket,
    place_polymarket_limit, get_polymarket_positions,
    cancel_polymarket_order, cancel_all_polymarket_orders,
)
from scrapers.aster_scraper import (
    aster_ticker, aster_orderbook, aster_klines, aster_funding_rate,
    aster_balance, aster_positions, aster_place_order, aster_cancel_order,
    aster_open_orders, aster_set_leverage, aster_diagnose,
)


# ════════════════════════════════════════════════════════════════
# LLM AUTO-DETECTION
# ════════════════════════════════════════════════════════════════

_PROVIDERS = {
    "ANTHROPIC_API_KEY":  ("anthropic",  "claude-sonnet-4-5"),
    "OPENAI_API_KEY":     ("openai",     "gpt-4.1"),
    "GEMINI_API_KEY":     ("gemini",     "gemini-2.5-flash"),
    "XAI_API_KEY":        ("xai",        "grok-3-fast"),
}

_ENDPOINTS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "xai":    "https://api.x.ai/v1",
}


def _detect_model():
    """Detect available LLM provider from environment."""
    # Check v2-style LLM_API_KEY first
    provider_name = os.getenv("LLM_PROVIDER", "").upper()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if api_key:
        provider_map = {
            "CLAUDE": "anthropic",
            "GEMINI": "gemini",
            "GROK": "xai",
        }
        p = provider_map.get(provider_name, "anthropic")
        model_map = {
            "anthropic": "claude-sonnet-4-5",
            "gemini": "gemini-2.5-flash",
            "xai": "grok-3-fast",
        }
        return p, model_map.get(p, "claude-sonnet-4-5"), api_key

    # Fall back to v1-style individual provider keys
    for env_var, (provider, default_model) in _PROVIDERS.items():
        key = os.environ.get(env_var, "").strip()
        if key and key != "your-api-key-here":
            return provider, default_model, key
    return None, None, None


def _make_model(provider, model_id, api_key):
    """Create an Agno model object."""
    if provider == "anthropic":
        return Claude(id=model_id, api_key=api_key)
    endpoint = _ENDPOINTS.get(provider)
    return OpenAIChat(id=model_id, api_key=api_key, base_url=endpoint)


# ════════════════════════════════════════════════════════════════
# X/TWITTER WRAPPERS
# ════════════════════════════════════════════════════════════════

def _search_tweets(query: str, max_tweets: int = 50) -> list:
    """Search recent tweets by keyword."""
    x = XScraper()
    return x.search_tweets(query, max_tweets)


def _get_trending_topics() -> list:
    """Get worldwide trending topics on X/Twitter."""
    x = XScraper()
    return x.get_trending_topics()


# ════════════════════════════════════════════════════════════════
# CAPTAIN INSTRUCTIONS
# ════════════════════════════════════════════════════════════════

CAPTAIN_INSTRUCTIONS = """You are the Captain of an institutional-grade financial intelligence team.
You coordinate 4 specialist agents.

## Your Team
- **Analyst** — crypto prices (CoinGecko), macro (FRED), news sentiment (Y2), social (Elfa AI, X/Twitter)
- **Trader** — executes trades on Hyperliquid, Aster DEX, and Polymarket
- **Risk Manager** — position monitoring, sizing, guardrails across all venues
- **Ops** — data export, file operations, reporting

## Routing Rules
1. Price/research/news/sentiment → Analyst
2. Trade execution → Trader (ALWAYS confirm with user first)
3. Risk/sizing/portfolio → Risk Manager
4. File/report operations → Ops
5. Complex queries → delegate to multiple agents, synthesize results

## Rules
- Be quantitative — cite numbers, percentages, exact values
- ⚠️ NEVER auto-execute trades — always confirm with user
- Provide clear, structured responses
"""


# ════════════════════════════════════════════════════════════════
# SPECIALIST AGENT BUILDERS
# ════════════════════════════════════════════════════════════════

def _create_analyst(model) -> Agent:
    """Analyst — market research, macro, sentiment."""
    return Agent(
        name="Analyst",
        role="Market Research, Macro & Sentiment Specialist",
        model=model,
        tools=[
            # Crypto
            get_crypto_price, get_crypto_top_n, search_crypto,
            # FRED macro
            get_fred_series, get_economic_dashboard,
            # Y2 News
            get_news_sentiment, get_news_recap,
            # Elfa AI social
            get_trending_tokens, get_social_mentions,
            # X/Twitter
            _search_tweets, _get_trending_topics,
        ],
        instructions=[
            "You are the Analyst on an institutional-grade financial intelligence team.",
            "Use CoinGecko for crypto prices. Use FRED for macro (GDP, CPI, rates, VIX).",
            "Use Y2 for news sentiment. Use Elfa AI for trending tokens and social mentions.",
            "Use X/Twitter for tweet sentiment analysis.",
            "Be quantitative. Cite specific numbers, changes, and percentages.",
            "Flag anything unusual — divergences, extreme sentiment, macro shifts.",
            "You do NOT execute trades. You provide analysis for the Trader and Risk Manager.",
        ],
        markdown=True,
        add_datetime_to_context=True,
    )


def _create_trader(model) -> Agent:
    """Trader — execution across HL, Aster, Polymarket."""
    return Agent(
        name="Trader",
        role="Trade Execution Specialist — Hyperliquid, Aster DEX & Polymarket",
        model=model,
        tools=[
            # Hyperliquid
            get_hl_config, get_hl_account_info, get_hl_positions,
            get_hl_orderbook, get_hl_open_orders,
            # Aster DEX
            aster_ticker, aster_orderbook, aster_klines, aster_funding_rate,
            aster_balance, aster_positions, aster_place_order, aster_cancel_order,
            aster_open_orders, aster_set_leverage,
            # Polymarket
            get_polymarket_markets, search_polymarket, get_polymarket_orderbook,
            get_polymarket_price, buy_polymarket, sell_polymarket,
            place_polymarket_limit, get_polymarket_positions,
            cancel_polymarket_order, cancel_all_polymarket_orders,
        ],
        instructions=[
            "You are the Trader on an institutional-grade financial intelligence team.",
            "Execute trades on Hyperliquid (perps), Aster DEX (futures), and Polymarket (predictions).",
            "",
            "⚠️ CRITICAL RULES:",
            "  1. ALWAYS confirm with the user before placing any trade.",
            "  2. Show the exact order details BEFORE executing.",
            "  3. This involves REAL MONEY — never auto-execute.",
            "",
            "You do NOT analyze markets. Defer analysis to the Analyst.",
            "You do NOT manage risk. Defer sizing to the Risk Manager.",
        ],
        markdown=True,
        add_datetime_to_context=True,
    )


def _create_risk_manager(model) -> Agent:
    """Risk Manager — positions, sizing, guardrails."""
    return Agent(
        name="Risk Manager",
        role="Portfolio Risk & Position Sizing Specialist",
        model=model,
        tools=[
            # Cross-venue position monitoring
            get_hl_account_info, get_hl_positions, get_hl_open_orders,
            aster_balance, aster_positions, aster_open_orders,
            get_polymarket_positions,
            # Market context
            get_crypto_price,
            get_economic_dashboard,
        ],
        instructions=[
            "You are the Risk Manager on an institutional-grade team.",
            "Monitor positions across ALL venues: Hyperliquid, Aster DEX, Polymarket.",
            "",
            "RISK RULES:",
            "  • Max 2% of equity risked per trade (unless user overrides)",
            "  • Max 10x leverage on any single position",
            "  • Flag positions > 20% of equity",
            "  • Alert when unrealized drawdown > 10% of equity",
            "",
            "Always provide specific numbers. Be conservative by default.",
            "You do NOT execute trades — flag concerns for the Captain and Trader.",
        ],
        markdown=True,
        add_datetime_to_context=True,
    )


def _create_ops(model) -> Agent:
    """Ops — data export, diagnostics, reporting."""
    return Agent(
        name="Ops",
        role="Infrastructure & Data Operations",
        model=model,
        tools=[
            aster_diagnose,
        ],
        instructions=[
            "You are the Ops agent — handles diagnostics, data export, and reporting.",
            "Use aster_diagnose to check DEX connectivity.",
            "Help format and export data when requested.",
            "Coordinate with other agents to compile comprehensive reports.",
        ],
        markdown=True,
    )


# ════════════════════════════════════════════════════════════════
# SWARM ASSEMBLER
# ════════════════════════════════════════════════════════════════

def create_swarm() -> Team:
    """Build and return the 5-agent Agno swarm team."""
    provider, model_id, api_key = _detect_model()
    if not provider:
        raise ValueError(
            "No LLM API key found. Set LLM_API_KEY in .env, "
            "or set ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, or XAI_API_KEY."
        )

    model_fn = lambda: _make_model(provider, model_id, api_key)

    captain = Agent(
        name="Captain",
        role="Team Leader & Request Router",
        model=model_fn(),
        instructions=[CAPTAIN_INSTRUCTIONS],
        markdown=True,
        add_datetime_to_context=True,
    )

    analyst = _create_analyst(model_fn())
    trader = _create_trader(model_fn())
    risk_mgr = _create_risk_manager(model_fn())
    ops = _create_ops(model_fn())

    team = Team(
        name="Hyper Sentinel v2 Swarm",
        mode="coordinate",
        model=model_fn(),
        members=[captain, analyst, trader, risk_mgr, ops],
        instructions=[CAPTAIN_INSTRUCTIONS],
        markdown=True,
        show_members_responses=True,
    )

    return team


# ════════════════════════════════════════════════════════════════
# SWARM WRAPPER (for main.py compatibility)
# ════════════════════════════════════════════════════════════════

class SwarmAgent:
    """Wrapper that exposes .chat() and .clear() for the REPL."""

    def __init__(self):
        self.team = create_swarm()
        self.history = []

    def chat(self, message: str) -> str:
        self.history.append({"role": "user", "content": message})
        response = self.team.run(message)
        text = response.content if hasattr(response, "content") else str(response)
        self.history.append({"role": "assistant", "content": text})
        return text

    def clear(self):
        self.history = []
        self.team = create_swarm()
