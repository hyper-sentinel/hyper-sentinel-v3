"""
Sentinel v3 — Upsonic Tool Wrappers

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


# ── Tool Groups ──────────────────────────────────────────────────────

CRYPTO_TOOLS = [get_crypto_price, get_crypto_top_n, search_crypto]

MACRO_TOOLS = [get_economic_dashboard, get_fred_series]

SENTIMENT_TOOLS = [get_y2_recap, get_y2_sentiment, get_trending_tokens, get_social_mentions, search_x]

TRADING_TOOLS = [
    get_hl_account, get_hl_positions, get_hl_orderbook,
    get_aster_ticker, get_aster_positions, get_aster_balance,
    search_polymarket, get_polymarket_positions,
]

ALL_TOOLS = CRYPTO_TOOLS + MACRO_TOOLS + SENTIMENT_TOOLS + TRADING_TOOLS
