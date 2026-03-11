"""
Trader Agent — Executes trades across DEXes and prediction markets.

Tools:
  - Hyperliquid: Direct function tools (8 tools)
  - Aster DEX: Direct function tools (16 tools — futures trading, market data, leverage)
  - Polymarket: Direct function tools (11 tools)
"""

from agno.agent import Agent

from scrapers.hyperliquid_scraper import (
    get_hl_config, get_hl_account_info, get_hl_positions, get_hl_orderbook,
    get_hl_open_orders, place_hl_order, cancel_hl_order, close_hl_position,
)
from scrapers.aster_scraper import (
    aster_ping, aster_ticker, aster_orderbook, aster_klines,
    aster_funding_rate, aster_exchange_info, aster_config,
    aster_balance, aster_positions, aster_account_info,
    aster_place_order, aster_cancel_order, aster_cancel_all_orders,
    aster_open_orders, aster_set_leverage, aster_set_margin_mode,
    aster_place_order_confirmed, aster_countdown_cancel,
    aster_place_trailing_stop,
)
from scrapers.polymarket_scraper import (
    get_polymarket_markets, search_polymarket, get_polymarket_orderbook,
    get_polymarket_price, buy_polymarket, sell_polymarket,
    place_polymarket_limit, get_polymarket_positions,
    cancel_polymarket_order, cancel_all_polymarket_orders,
)


def create_trader_agent(model) -> Agent:
    """Create the Trader specialist agent with direct Aster DEX integration."""

    return Agent(
        name="Trader",
        role="Trade Execution Specialist — Hyperliquid, Aster DEX, Polymarket",
        model=model,
        tools=[
            # Hyperliquid — direct function tools (8)
            get_hl_config,
            get_hl_account_info,
            get_hl_positions,
            get_hl_orderbook,
            get_hl_open_orders,
            place_hl_order,
            cancel_hl_order,
            close_hl_position,
            # Aster DEX — direct function tools (16)
            aster_ping,
            aster_ticker,
            aster_orderbook,
            aster_klines,
            aster_funding_rate,
            aster_exchange_info,
            aster_config,
            aster_balance,
            aster_positions,
            aster_account_info,
            aster_place_order,
            aster_cancel_order,
            aster_cancel_all_orders,
            aster_open_orders,
            aster_set_leverage,
            aster_set_margin_mode,
            aster_place_order_confirmed,
            aster_countdown_cancel,
            aster_place_trailing_stop,
            # Polymarket — direct function tools (11)
            get_polymarket_markets,
            search_polymarket,
            get_polymarket_orderbook,
            get_polymarket_price,
            buy_polymarket,
            sell_polymarket,
            place_polymarket_limit,
            get_polymarket_positions,
            cancel_polymarket_order,
            cancel_all_polymarket_orders,
        ],
        instructions=[
            "You are the Trader on a crypto trading team.",
            "Your job: execute trades precisely across Hyperliquid, Aster DEX, and Polymarket.",
            "",
            "You have access to THREE trading venues:",
            "  • Hyperliquid — Perp futures (BTC, ETH, SOL, 200+ pairs) via direct tools",
            "  • Aster DEX — Futures via direct tools (aster_* functions)",
            "  • Polymarket — Prediction markets (politics, crypto, sports)",
            "",
            "ASTER DEX TOOLS:",
            "  Market Data: aster_ping, aster_ticker, aster_orderbook, aster_klines,",
            "               aster_funding_rate, aster_exchange_info",
            "  Account:     aster_config, aster_balance, aster_positions, aster_account_info",
            "  Trading:     aster_place_order, aster_cancel_order, aster_cancel_all_orders,",
            "               aster_open_orders",
            "  Leverage:    aster_set_leverage, aster_set_margin_mode",
            "",
            "⚠️ CRITICAL RULES:",
            "  1. ALWAYS confirm with the user before executing ANY trade.",
            "  2. State the exact order: venue, direction, size, price, leverage.",
            "  3. Wait for explicit 'yes' or 'confirm' before placing.",
            "  4. After execution, report fill price and order ID.",
            "",
            "For market data (prices, orderbook), you can act freely.",
            "For trade execution, you MUST get confirmation first.",
        ],
        markdown=True,
        add_datetime_to_context=True,
    )
