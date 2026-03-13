"""
Sentinel — Upsonic Tool Wrappers

Wraps all v1 scrapers as Upsonic @tool functions so the Team agents
can call real APIs instead of hallucinating data.

Usage:
    from tools import CRYPTO_TOOLS, MACRO_TOOLS, TRADING_TOOLS, ALL_TOOLS
    task = Task(description="...", tools=CRYPTO_TOOLS)
"""

from upsonic.tools import tool


# ── Crypto (CoinGecko — always available) ────────────────────────────

@tool
def get_crypto_price(coin_id: str) -> dict:
    """Get current price for a cryptocurrency from CoinGecko. Use 'bitcoin', 'ethereum', 'solana', etc."""
    from scrapers.crypto_scraper import get_crypto_price as _fn
    return _fn(coin_id)

@tool
def get_crypto_top_n(n: int = 10) -> list:
    """Get top N cryptocurrencies by market cap from CoinGecko."""
    from scrapers.crypto_scraper import get_top_cryptos as _fn
    return _fn(n)

@tool
def search_crypto(query: str) -> list:
    """Search for a cryptocurrency by name or symbol on CoinGecko."""
    from scrapers.crypto_scraper import search_coins as _fn
    return _fn(query)


# ── FRED (Macro — requires FRED_API_KEY) ─────────────────────────────

@tool
def get_economic_dashboard() -> dict:
    """Get FRED macro dashboard: GDP, CPI, unemployment, fed funds rate, VIX, 10Y-2Y spread."""
    from scrapers.fred_scraper import get_economic_dashboard as _fn
    return _fn()

@tool
def get_fred_series(series_id: str) -> dict:
    """Get a specific FRED series by ID. Common IDs: FEDFUNDS, CPIAUCSL, GDP, UNRATE, T10Y2Y, VIXCLS."""
    from scrapers.fred_scraper import get_series_latest as _fn
    return _fn(series_id)


# ── Y2 Intelligence (requires Y2_API_KEY) ────────────────────────────

@tool
def get_y2_recap(ticker: str = "BTC") -> dict:
    """Get Y2 Intelligence recap report for a ticker."""
    from scrapers.y2_scraper import get_news_recap as _fn
    return _fn(ticker)

@tool
def get_y2_sentiment(ticker: str = "BTC") -> dict:
    """Get Y2 Intelligence sentiment analysis for a ticker."""
    from scrapers.y2_scraper import get_news_sentiment as _fn
    return _fn(ticker)

@tool
def get_y2_reports() -> list:
    """Get latest Y2 Intelligence reports."""
    from scrapers.y2_scraper import get_intelligence_reports as _fn
    return _fn()

@tool
def get_y2_report_detail(report_id: str) -> dict:
    """Get full details of a Y2 Intelligence report by ID."""
    from scrapers.y2_scraper import get_report_detail as _fn
    return _fn(report_id)


# ── Elfa AI (requires ELFA_API_KEY) ──────────────────────────────────

@tool
def get_trending_tokens() -> list:
    """Get trending tokens from Elfa AI social analysis."""
    from scrapers.elfa_scraper import get_trending_tokens as _fn
    return _fn()

@tool
def get_social_mentions(query: str) -> dict:
    """Get social media mentions for a search query from Elfa AI."""
    from scrapers.elfa_scraper import get_top_mentions as _fn
    return _fn(query)

@tool
def get_trending_narratives() -> list:
    """Get trending crypto narratives from Elfa AI."""
    from scrapers.elfa_scraper import get_trending_narratives as _fn
    return _fn()

@tool
def get_token_news(token: str) -> list:
    """Get news for a specific token from Elfa AI."""
    from scrapers.elfa_scraper import get_token_news as _fn
    return _fn(token)

@tool
def search_social_mentions(query: str) -> list:
    """Search social media mentions by keyword from Elfa AI."""
    from scrapers.elfa_scraper import search_mentions as _fn
    return _fn(query)


# ── X / Twitter (requires X_BEARER_TOKEN) ────────────────────────────

@tool
def search_x(query: str, max_results: int = 10) -> list:
    """Search recent tweets on X (Twitter) for a query."""
    import os as _os
    try:
        from scrapers.x_scraper import XScraper
        token = _os.getenv("X_BEARER_TOKEN", "")
        if not token:
            return {"error": "X_BEARER_TOKEN not set"}
        return XScraper(token).search_tweets(query, max_results)
    except Exception as e:
        return {"error": str(e)}


# ── Hyperliquid (requires HL keys) ───────────────────────────────────

@tool
def get_hl_account() -> dict:
    """Get Hyperliquid account info: equity, margin, positions."""
    from scrapers.hyperliquid_scraper import get_hl_account_info as _fn
    return _fn()

@tool
def get_hl_positions() -> list:
    """Get all open Hyperliquid perpetual positions."""
    from scrapers.hyperliquid_scraper import get_hl_positions as _fn
    return _fn()

@tool
def get_hl_orderbook(symbol: str) -> dict:
    """Get Hyperliquid order book for a symbol (e.g. 'BTC')."""
    from scrapers.hyperliquid_scraper import get_hl_orderbook as _fn
    return _fn(symbol)

@tool
def get_hl_config() -> dict:
    """Get Hyperliquid connection config: wallet address, trading status."""
    from scrapers.hyperliquid_scraper import get_hl_config as _fn
    return _fn()

@tool
def get_hl_open_orders() -> list:
    """Get all open/pending Hyperliquid orders."""
    from scrapers.hyperliquid_scraper import get_hl_open_orders as _fn
    return _fn()

@tool
def place_hl_order(coin: str, side: str, size: float, price: float = 0, order_type: str = "market") -> dict:
    """Place a Hyperliquid perp order. side='buy'|'sell', order_type='market'|'limit'. ⚠️ REAL TRADING."""
    from scrapers.hyperliquid_scraper import place_hl_order as _fn
    return _fn(coin=coin, side=side, size=size, price=price, order_type=order_type)

@tool
def cancel_hl_order(coin: str, oid: str) -> dict:
    """Cancel a Hyperliquid order by coin and order ID."""
    from scrapers.hyperliquid_scraper import cancel_hl_order as _fn
    return _fn(coin=coin, oid=oid)

@tool
def close_hl_position(coin: str) -> dict:
    """Close an entire Hyperliquid position at market price. ⚠️ REAL TRADING."""
    from scrapers.hyperliquid_scraper import close_hl_position as _fn
    return _fn(coin=coin)


# ── Aster DEX (requires ASTER keys) ─────────────────────────────────

@tool
def get_aster_ticker(symbol: str = "BTCUSDT") -> dict:
    """Get Aster DEX ticker data for a futures symbol."""
    from scrapers.aster_scraper import aster_ticker as _fn
    return _fn(symbol)

@tool
def get_aster_positions() -> list:
    """Get all open Aster DEX futures positions."""
    from scrapers.aster_scraper import aster_positions as _fn
    return _fn()

@tool
def get_aster_balance() -> dict:
    """Get Aster DEX account balance and equity."""
    from scrapers.aster_scraper import aster_balance as _fn
    return _fn()

@tool
def get_aster_orderbook(symbol: str = "BTCUSDT", limit: int = 10) -> dict:
    """Get Aster DEX order book for a futures symbol."""
    from scrapers.aster_scraper import aster_orderbook as _fn
    return _fn(symbol, limit)

@tool
def get_aster_klines(symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 50) -> list:
    """Get Aster DEX candlestick data. Intervals: 1m, 5m, 15m, 1h, 4h, 1d."""
    from scrapers.aster_scraper import aster_klines as _fn
    return _fn(symbol, interval, limit)

@tool
def get_aster_funding_rate(symbol: str = "BTCUSDT") -> dict:
    """Get current Aster DEX funding rate for a symbol."""
    from scrapers.aster_scraper import aster_funding_rate as _fn
    return _fn(symbol)

@tool
def place_aster_order(symbol: str, side: str, quantity: float = 0, order_type: str = "MARKET", price: float = 0, usd_amount: float = 0) -> dict:
    """Place an Aster DEX futures order. side='BUY'|'SELL'. Use usd_amount for dollar-sized orders (e.g. 110 = $110 worth of margin), or quantity for raw contract size (e.g. 0.001 BTC). ⚠️ REAL TRADING."""
    from scrapers.aster_scraper import aster_place_order as _fn
    return _fn(symbol=symbol, side=side, quantity=quantity, order_type=order_type, price=price if price else None, usd_amount=usd_amount if usd_amount else None)

@tool
def cancel_aster_order(symbol: str, order_id: str) -> dict:
    """Cancel an Aster DEX order."""
    from scrapers.aster_scraper import aster_cancel_order as _fn
    return _fn(symbol=symbol, order_id=order_id)

@tool
def set_aster_leverage(symbol: str, leverage: int) -> dict:
    """Set leverage for an Aster DEX symbol."""
    from scrapers.aster_scraper import aster_set_leverage as _fn
    return _fn(symbol=symbol, leverage=leverage)


# ── Polymarket (requires PM keys) ────────────────────────────────────

@tool
def search_polymarket(query: str) -> list:
    """Search Polymarket prediction markets by query."""
    from scrapers.polymarket_scraper import search_polymarket as _fn
    return _fn(query)

@tool
def get_polymarket_positions() -> list:
    """Get your open Polymarket positions."""
    from scrapers.polymarket_scraper import get_polymarket_positions as _fn
    return _fn()

@tool
def get_polymarket_markets() -> list:
    """Get active Polymarket prediction markets."""
    from scrapers.polymarket_scraper import get_polymarket_markets as _fn
    return _fn()

@tool
def get_polymarket_price(token_id: str) -> dict:
    """Get current price for a Polymarket token."""
    from scrapers.polymarket_scraper import get_polymarket_price as _fn
    return _fn(token_id)

@tool
def get_polymarket_orderbook(token_id: str) -> dict:
    """Get Polymarket order book for a token."""
    from scrapers.polymarket_scraper import get_polymarket_orderbook as _fn
    return _fn(token_id)

@tool
def buy_polymarket(token_id: str, amount: float, price: float) -> dict:
    """Buy shares on Polymarket. ⚠️ REAL TRADING."""
    from scrapers.polymarket_scraper import buy_polymarket as _fn
    return _fn(token_id=token_id, amount=amount, price=price)

@tool
def sell_polymarket(token_id: str, amount: float, price: float) -> dict:
    """Sell shares on Polymarket. ⚠️ REAL TRADING."""
    from scrapers.polymarket_scraper import sell_polymarket as _fn
    return _fn(token_id=token_id, amount=amount, price=price)

@tool
def cancel_polymarket_order(order_id: str) -> dict:
    """Cancel a Polymarket order by ID."""
    from scrapers.polymarket_scraper import cancel_polymarket_order as _fn
    return _fn(order_id=order_id)


# ── Tool Groups ──────────────────────────────────────────────────────

CRYPTO_TOOLS = [get_crypto_price, get_crypto_top_n, search_crypto]

MACRO_TOOLS = [get_economic_dashboard, get_fred_series]

SENTIMENT_TOOLS = [
    get_y2_recap, get_y2_sentiment, get_y2_reports, get_y2_report_detail,
    get_trending_tokens, get_social_mentions, get_trending_narratives, get_token_news, search_social_mentions,
    search_x,
]

HL_TOOLS = [
    get_hl_account, get_hl_positions, get_hl_orderbook, get_hl_config, get_hl_open_orders,
    place_hl_order, cancel_hl_order, close_hl_position,
]

ASTER_TOOLS = [
    get_aster_ticker, get_aster_positions, get_aster_balance,
    get_aster_orderbook, get_aster_klines, get_aster_funding_rate,
    place_aster_order, cancel_aster_order, set_aster_leverage,
]

PM_TOOLS = [
    search_polymarket, get_polymarket_positions, get_polymarket_markets,
    get_polymarket_price, get_polymarket_orderbook,
    buy_polymarket, sell_polymarket, cancel_polymarket_order,
]

TRADING_TOOLS = HL_TOOLS + ASTER_TOOLS + PM_TOOLS

ALL_TOOLS = CRYPTO_TOOLS + MACRO_TOOLS + SENTIMENT_TOOLS + TRADING_TOOLS
