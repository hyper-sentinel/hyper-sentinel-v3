"""
Sentinel REST API v3 — Auto-generated endpoints from ToolRegistry.

Every tool registered in tools.py becomes a POST endpoint:
    POST /api/v1/tools/{tool_name}  →  execute tool  →  JSON response

Features:
    • Auto-generated from all 20+ tools (same tools as terminal)
    • API key auth for trading/account tools
    • Rate limiting per key
    • Swagger docs at /docs
    • Health check at /health

Run:
    uv run python api_server.py
    # → http://localhost:8000/docs
"""

import json
import os
import time
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

# Import tool registry + raw scraper functions (bypasses Upsonic @tool decorators)
from tool_registry import ToolRegistry

from scrapers.crypto_scraper import get_crypto_price, get_crypto_top_n, search_crypto
from scrapers.fred_scraper import get_fred_series, search_fred, get_economic_dashboard
from scrapers.y2_scraper import get_news_sentiment, get_news_recap, get_intelligence_reports, get_report_detail
from scrapers.elfa_scraper import (
    get_trending_tokens, get_top_mentions, search_mentions,
    get_trending_narratives, get_token_news,
)
# x_scraper is class-based — create standalone wrappers
import os as _os
def search_x(query: str, max_results: int = 10) -> list:
    """Search recent tweets on X (Twitter) for a query."""
    try:
        from scrapers.x_scraper import XScraper
        token = _os.getenv("X_BEARER_TOKEN", "")
        if not token:
            return {"error": "X_BEARER_TOKEN not set in .env"}
        client = XScraper(token)
        return client.search_tweets(query, max_results)
    except Exception as e:
        return {"error": f"X search failed: {str(e)}"}
from scrapers.hyperliquid_scraper import (
    get_hl_config, get_hl_account_info, get_hl_positions,
    get_hl_orderbook, get_hl_open_orders,
    place_hl_order, cancel_hl_order, close_hl_position,
)
from scrapers.aster_scraper import (
    aster_diagnose, aster_ping, aster_ticker, aster_orderbook,
    aster_klines, aster_funding_rate, aster_exchange_info,
    aster_balance, aster_positions, aster_account_info,
    aster_place_order, aster_cancel_order, aster_cancel_all_orders,
    aster_open_orders, aster_set_leverage,
)
from scrapers.polymarket_scraper import (
    get_polymarket_markets, search_polymarket, get_polymarket_orderbook,
    get_polymarket_price, get_polymarket_positions,
    buy_polymarket, sell_polymarket, place_polymarket_limit,
    cancel_polymarket_order, cancel_all_polymarket_orders,
)

# ============================================================================
# Build Registry — 45+ tools
# ============================================================================

registry = ToolRegistry()

# Crypto (CoinGecko — free)
registry.register(get_crypto_price, get_crypto_top_n, search_crypto)

# FRED Macro (free key)
registry.register(get_fred_series, search_fred, get_economic_dashboard)

# Y2 Intelligence
registry.register(get_news_sentiment, get_news_recap, get_intelligence_reports, get_report_detail)

# Elfa AI
registry.register(get_trending_tokens, get_top_mentions, search_mentions, get_trending_narratives, get_token_news)

# X / Twitter
registry.register(search_x)

# Hyperliquid
registry.register(
    get_hl_config, get_hl_account_info, get_hl_positions,
    get_hl_orderbook, get_hl_open_orders,
    place_hl_order, cancel_hl_order, close_hl_position,
)

# Aster DEX
registry.register(
    aster_diagnose, aster_ping, aster_ticker, aster_orderbook,
    aster_klines, aster_funding_rate, aster_exchange_info,
    aster_balance, aster_positions, aster_account_info,
    aster_place_order, aster_cancel_order, aster_cancel_all_orders,
    aster_open_orders, aster_set_leverage,
)

# Polymarket
registry.register(
    get_polymarket_markets, search_polymarket, get_polymarket_orderbook,
    get_polymarket_price, get_polymarket_positions,
    buy_polymarket, sell_polymarket, place_polymarket_limit,
    cancel_polymarket_order, cancel_all_polymarket_orders,
)

# ============================================================================
# Config
# ============================================================================

API_PORT = int(os.getenv("API_PORT", "8000"))
API_HOST = os.getenv("API_HOST", "0.0.0.0")

# API keys — comma-separated list in .env
# Format: API_KEYS=sk-key1,sk-key2,sk-key3
_raw_keys = os.getenv("API_KEYS", "").strip()
VALID_API_KEYS = set(k.strip() for k in _raw_keys.split(",") if k.strip()) if _raw_keys else set()

# Rate limiting
RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT", "60"))

# Public tools — no API key required (read-only market data)
PUBLIC_TOOLS = {
    # Crypto prices (free, no auth)
    "get_crypto_price", "get_crypto_top_n", "search_crypto",
    # FRED macro (free key)
    "get_economic_dashboard", "get_fred_series", "search_fred",
    # Y2 Intelligence
    "get_news_sentiment", "get_news_recap", "get_intelligence_reports", "get_report_detail",
    # Elfa AI
    "get_trending_tokens", "get_top_mentions", "search_mentions",
    "get_trending_narratives", "get_token_news",
    # Twitter
    "search_x",
    # Aster public market data
    "aster_ping", "aster_ticker", "aster_orderbook",
    "aster_klines", "aster_funding_rate", "aster_exchange_info",
    # Hyperliquid public
    "get_hl_orderbook", "get_hl_config",
    # Polymarket public
    "get_polymarket_markets", "search_polymarket",
    "get_polymarket_orderbook", "get_polymarket_price",
}


# ============================================================================
# Rate Limiter (in-memory, per API key)
# ============================================================================

class RateLimiter:
    """Simple sliding-window rate limiter."""

    def __init__(self, max_per_minute: int = 60):
        self.max_per_minute = max_per_minute
        self._calls: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> bool:
        """Return True if allowed, False if rate limited."""
        now = time.time()
        window_start = now - 60
        self._calls[key] = [t for t in self._calls[key] if t > window_start]
        if len(self._calls[key]) >= self.max_per_minute:
            return False
        self._calls[key].append(now)
        return True

    def remaining(self, key: str) -> int:
        now = time.time()
        window_start = now - 60
        recent = [t for t in self._calls[key] if t > window_start]
        return max(0, self.max_per_minute - len(recent))


rate_limiter = RateLimiter(max_per_minute=RATE_LIMIT_PER_MINUTE)


# ============================================================================
# FastAPI App
# ============================================================================

def create_app() -> "FastAPI":
    app = FastAPI(
        title="🛡️ Sentinel API",
        description=(
            "REST API for Hyper-Sentinel v3 — 45+ crypto trading, intelligence, and analysis tools.\n\n"
            "**Public tools** (no auth): crypto prices, social sentiment, news, macro data.\n\n"
            "**Auth-required tools** (X-API-Key header): DEX trading, account balances, order management."
        ),
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — allow all origins for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Auth helpers ──────────────────────────────────────────

    def _get_api_key(request: Request) -> str | None:
        """Extract API key from X-API-Key header."""
        return request.headers.get("X-API-Key")

    def _require_auth(tool_name: str, api_key: str | None):
        """Check auth for non-public tools."""
        if tool_name in PUBLIC_TOOLS:
            return  # Public — no auth needed
        if not VALID_API_KEYS:
            return  # No keys configured — allow all (dev mode)
        if not api_key or api_key not in VALID_API_KEYS:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Unauthorized",
                    "message": "Valid X-API-Key header required for this tool.",
                    "tool": tool_name,
                    "is_public": False,
                },
            )

    def _check_rate_limit(api_key: str | None, request: Request):
        """Apply rate limiting."""
        key = api_key or (request.client.host if request.client else "anonymous")
        if not rate_limiter.check(key):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": RATE_LIMIT_PER_MINUTE,
                    "remaining": 0,
                    "retry_after_seconds": 60,
                },
            )

    # ── Routes ────────────────────────────────────────────────

    @app.get("/", tags=["Meta"])
    async def root():
        """API info and tool count."""
        return {
            "name": "Sentinel API",
            "version": "3.0.0",
            "tools": registry.tool_count,
            "public_tools": len(PUBLIC_TOOLS),
            "auth_required_tools": registry.tool_count - len(PUBLIC_TOOLS),
            "docs": "/docs",
            "endpoints": {
                "list_tools": "GET /api/v1/tools",
                "tool_info": "GET /api/v1/tools/{tool_name}",
                "call_tool": "POST /api/v1/tools/{tool_name}",
                "health": "GET /health",
            },
        }

    @app.get("/health", tags=["Meta"])
    async def health():
        """Health check."""
        return {"status": "ok", "tools": registry.tool_count}

    @app.get("/api/v1/tools", tags=["Tools"])
    async def list_tools():
        """List all available tools with their schemas and auth requirements."""
        tools = []
        for spec in registry.specs():
            tools.append({
                "name": spec["name"],
                "description": spec["description"],
                "parameters": spec["parameters"],
                "auth_required": spec["name"] not in PUBLIC_TOOLS,
            })
        return {"count": len(tools), "tools": tools}

    @app.get("/api/v1/tools/{tool_name}", tags=["Tools"])
    async def tool_info(tool_name: str):
        """Get schema and info for a specific tool."""
        for spec in registry.specs():
            if spec["name"] == tool_name:
                return {
                    "name": spec["name"],
                    "description": spec["description"],
                    "parameters": spec["parameters"],
                    "auth_required": spec["name"] not in PUBLIC_TOOLS,
                    "usage": {
                        "method": "POST",
                        "url": f"/api/v1/tools/{tool_name}",
                        "body": "JSON object matching the parameters schema",
                        "headers": {"X-API-Key": "required"} if spec["name"] not in PUBLIC_TOOLS else {},
                    },
                }
        raise HTTPException(status_code=404, detail={"error": f"Tool '{tool_name}' not found"})

    @app.post("/api/v1/tools/{tool_name}", tags=["Tools"])
    async def call_tool(tool_name: str, request: Request):
        """Execute a tool by name. Pass arguments as JSON body."""
        # Validate tool exists
        if tool_name not in registry.tool_names:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Tool '{tool_name}' not found",
                    "available": registry.tool_names,
                },
            )

        # Auth check
        api_key = _get_api_key(request)
        _require_auth(tool_name, api_key)

        # Rate limit
        _check_rate_limit(api_key, request)

        # Parse body
        try:
            body = await request.json()
        except Exception:
            body = {}

        # Execute
        result_str = registry.execute(tool_name, body)

        try:
            result = json.loads(result_str)
        except json.JSONDecodeError:
            result = {"raw": result_str}

        # Check for errors from the tool
        if isinstance(result, dict) and "error" in result:
            return JSONResponse(status_code=400, content=result)

        return {
            "tool": tool_name,
            "result": result,
            "meta": {
                "rate_limit_remaining": rate_limiter.remaining(
                    api_key or (request.client.host if request.client else "anonymous")
                ),
            },
        }

    return app


# ============================================================================
# Entrypoint
# ============================================================================

if __name__ == "__main__":
    if not HAS_FASTAPI:
        print("❌ FastAPI not installed. Run: uv add fastapi uvicorn")
        exit(1)

    import uvicorn

    app = create_app()

    print(f"""
╔═══════════════════════════════════════════════════════╗
║            🛡️  Sentinel REST API v3  🛡️               ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║   Tools:    {registry.tool_count:<3} registered                         ║
║   Public:   {len(PUBLIC_TOOLS):<3} (no auth needed)                    ║
║   Private:  {registry.tool_count - len(PUBLIC_TOOLS):<3} (X-API-Key required)                ║
║   Rate:     {RATE_LIMIT_PER_MINUTE}/min per key                        ║
║                                                       ║
║   Swagger:  http://{API_HOST}:{API_PORT}/docs              ║
║   ReDoc:    http://{API_HOST}:{API_PORT}/redoc             ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
""")

    if not VALID_API_KEYS:
        print("  ⚠️  No API_KEYS set in .env — all tools are open (dev mode)")
        print("     Set API_KEYS=sk-your-key-here in .env for production\n")

    uvicorn.run(app, host=API_HOST, port=API_PORT)
