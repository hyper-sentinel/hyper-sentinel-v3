"""
Risk Manager Agent — Position sizing, PnL monitoring, risk controls.

Tools: Account info, positions from HL + Aster, portfolio calculations
"""

from agno.agent import Agent

from scrapers.hyperliquid_scraper import (
    get_hl_account_info, get_hl_positions, get_hl_open_orders,
)
from scrapers.aster_scraper import (
    aster_balance, aster_positions, aster_account_info, aster_open_orders,
)
from scrapers.fred_scraper import get_economic_dashboard


def create_risk_manager_agent(model) -> Agent:
    """Create the Risk Manager specialist agent."""
    return Agent(
        name="Risk Manager",
        role="Portfolio Risk & Position Sizing Specialist",
        model=model,
        tools=[
            # Hyperliquid account/positions
            get_hl_account_info,
            get_hl_positions,
            get_hl_open_orders,
            # Aster account/positions
            aster_balance,
            aster_positions,
            aster_account_info,
            aster_open_orders,
            # Macro context
            get_economic_dashboard,
        ],
        instructions=[
            "You are the Risk Manager on a crypto trading team.",
            "Your job: assess risk, size positions, and protect capital.",
            "",
            "CORE RESPONSIBILITIES:",
            "  1. Review all positions across Hyperliquid and Aster before trades.",
            "  2. Calculate position sizing based on account equity and risk tolerance.",
            "  3. Flag over-leveraged positions or concentrated exposure.",
            "  4. Recommend stop-loss levels based on volatility.",
            "  5. Monitor total portfolio PnL and drawdown.",
            "",
            "RISK RULES:",
            "  • Never recommend more than 5% of equity on a single trade.",
            "  • Flag if total leverage exceeds 3x across all venues.",
            "  • Warn if one asset is >30% of portfolio.",
            "  • Consider macro conditions (rates, VIX) for risk adjustments.",
            "",
            "You APPROVE or REJECT trade proposals from the Trader.",
            "If rejecting, explain why and suggest a safer alternative.",
        ],
        markdown=True,
        add_datetime_to_context=True,
    )
