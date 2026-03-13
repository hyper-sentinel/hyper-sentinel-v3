"""
Sentinel — Upsonic Team (Coordinate Mode)
==============================================
3 specialized agents with real tools, shared memory, thinking enabled.

Usage:
    from team import build_team, team_chat
    team = build_team()
    response = team_chat(team, "What's the BTC outlook?")

Or from the REPL:
    ⚡ You → team
    ✓ Team active!
    ⚡ Team → what is the price of bitcoin?
"""

import os
import logging

from upsonic import Agent, Task, Team

logger = logging.getLogger(__name__)

# ── Model resolution ─────────────────────────────────────────────

PROVIDER_MAP = {
    "CLAUDE": "anthropic/claude-sonnet-4-5",
    "GEMINI": "google/gemini-2.0-flash",
    "GROK": "xai/grok-2",
    "OLLAMA": "ollama/deepseek-r1:1.5b",
}


def _resolve_model() -> str:
    """Resolve LLM model from .env."""
    provider = os.getenv("LLM_PROVIDER", "CLAUDE").upper()
    custom = os.getenv("LLM_MODEL", "").strip()
    if custom:
        return custom
    return PROVIDER_MAP.get(provider, PROVIDER_MAP["CLAUDE"])


# ── Tool imports ─────────────────────────────────────────────────

def _get_tools():
    """Import tool groups. Lazy to avoid circular imports."""
    from core.tools import CRYPTO_TOOLS, MACRO_TOOLS, SENTIMENT_TOOLS, TRADING_TOOLS, ALL_TOOLS
    return {
        "crypto": CRYPTO_TOOLS,
        "macro": MACRO_TOOLS,
        "sentiment": SENTIMENT_TOOLS,
        "trading": TRADING_TOOLS,
        "all": ALL_TOOLS,
    }


# ── Agent Definitions ────────────────────────────────────────────

def _build_analyst(model: str, tools: dict) -> Agent:
    """Market research, macro analysis, sentiment tracking."""
    return Agent(
        name="Analyst",
        model=model,
        role="Senior Market Analyst",
        goal="Provide accurate, data-driven market analysis and research",
        instructions="""You are the Analyst for Hyper Sentinel, a crypto/fintech surveillance system.

YOUR RESPONSIBILITIES:
- Fetch REAL market data using your tools. NEVER make up prices.
- Monitor crypto prices, macro indicators (FRED), and social sentiment.
- Identify trends, anomalies, and regime changes.
- Flag any single-day move >5% on BTC/ETH/SOL as significant.
- Track FRED macro data (CPI, rates, VIX, yield curve) for regime shifts.

TOOLS YOU HAVE:
- get_crypto_price, get_crypto_top_n, search_crypto (CoinGecko)
- get_economic_dashboard, get_fred_series (FRED macro)
- get_y2_recap, get_y2_sentiment (Y2 Intelligence)
- get_trending_tokens, get_social_mentions (Elfa AI)
- search_x (Twitter/X)

Always cite exact numbers. Be concise. When uncertain, say so.""",
        tools=tools["crypto"] + tools["macro"] + tools["sentiment"],
        retry=2,
        enable_thinking_tool=True,
        show_tool_calls=True,
    )


def _build_risk_manager(model: str, tools: dict) -> Agent:
    """Risk assessment, position monitoring, guardrail enforcement."""
    return Agent(
        name="RiskManager",
        model=model,
        role="Risk & Compliance Officer",
        goal="Protect capital through rigorous risk assessment and position monitoring",
        instructions="""You are the Risk Manager for Hyper Sentinel.

YOUR RESPONSIBILITIES:
- Assess risk on any proposed trade or market condition.
- Monitor open positions across Hyperliquid and Aster DEX.
- Calculate position sizing based on account equity and risk tolerance.
- Enforce guardrails: max trade $100, max daily trades 5, max daily loss $250.
- Flag excessive leverage, concentrated positions, or correlation risk.
- Check macro conditions (FRED) that affect overall risk appetite.

TOOLS YOU HAVE:
- All crypto, macro, and sentiment tools for context
- get_hl_account, get_hl_positions (Hyperliquid positions)
- get_aster_positions, get_aster_balance (Aster positions)
- get_polymarket_positions (Polymarket exposure)

RULES:
- Never approve a trade exceeding guardrail limits.
- If kill switch is active, reject ALL trades.
- Always state the risk/reward ratio.
- Be conservative. When in doubt, recommend smaller position or no trade.""",
        tools=tools["all"],
        retry=2,
        enable_thinking_tool=True,
        show_tool_calls=True,
    )


def _build_trader(model: str, tools: dict) -> Agent:
    """Trade execution across Hyperliquid, Aster, and Polymarket."""
    return Agent(
        name="Trader",
        model=model,
        role="Execution Specialist",
        goal="Execute trades efficiently across DEXs with minimal slippage",
        instructions="""You are the Trader for Hyper Sentinel.

YOUR RESPONSIBILITIES:
- Execute trades on Hyperliquid (perps), Aster DEX (futures), and Polymarket (predictions).
- Check orderbook depth before execution to estimate slippage.
- Report fill prices, fees, and execution quality.
- Coordinate with RiskManager — never trade without risk approval.

TOOLS YOU HAVE:
- get_hl_account, get_hl_positions, get_hl_orderbook (Hyperliquid)
- get_aster_ticker, get_aster_positions, get_aster_balance (Aster)
- search_polymarket, get_polymarket_positions (Polymarket)

RULES:
- NEVER execute a trade without confirming guardrail compliance.
- Always report: symbol, side, size, price, fees.
- If auto-execute is OFF, present the trade plan but DO NOT execute.
- For information queries (prices, positions), just fetch and report.""",
        tools=tools["trading"],
        retry=2,
        show_tool_calls=True,
    )


# ── Team Builder ─────────────────────────────────────────────────

def build_team() -> Team:
    """
    Build the Upsonic Team in coordinate mode.

    Coordinate mode: a leader agent (same model) automatically
    routes tasks to the best specialist based on their role/goal.

    Returns:
        Team instance ready for team.do([Task(...)])
    """
    model = _resolve_model()
    tools = _get_tools()

    analyst = _build_analyst(model, tools)
    risk_mgr = _build_risk_manager(model, tools)
    trader = _build_trader(model, tools)

    team = Team(
        agents=[analyst, risk_mgr, trader],
        mode="coordinate",
        model=model,  # leader agent model
    )

    logger.info(f"Upsonic Team built: model={model}, mode=coordinate, agents=3")
    return team


def team_chat(team: Team, message: str) -> str:
    """
    Send a message to the team and get a response.
    The leader agent routes to the best specialist(s).
    """
    from core.tools import ALL_TOOLS
    task = Task(description=message, tools=ALL_TOOLS)
    result = team.do([task])
    return str(result) if result else "No response."
