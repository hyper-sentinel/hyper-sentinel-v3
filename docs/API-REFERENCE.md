# 🛡️ Sentinel API Documentation

> **Version 3.0.0** · REST API for Hyper-Sentinel — 49 crypto trading, intelligence, and analysis tools.

---

## Overview

The Sentinel API exposes the full power of Hyper-Sentinel as HTTP endpoints. Every tool available in the terminal agent — crypto prices, trading, social sentiment, macro data — is accessible via a simple REST API.

**Base URL:** `http://localhost:8000` (development) or your deployed URL

**Interactive Docs:** `{base_url}/docs` — Swagger UI with "Try it out" buttons

---

## Quick Start

### 1. Start the Server

```bash
cd hyper-sentinel-v3
uv run python api_server.py
```

### 2. Test It

```bash
# Health check
curl http://localhost:8000/health
# → {"status":"ok","tools":49}

# Get Bitcoin price
curl -X POST http://localhost:8000/api/v1/tools/get_crypto_price \
  -H "Content-Type: application/json" \
  -d '{"coin_id":"bitcoin"}'
```

### 3. Open the Dashboard

```bash
open http://localhost:8000/docs
```

---

## Authentication

The API uses two tiers:

| Tier | Auth Required | Tools |
|------|--------------|-------|
| **Public** | None | 28 tools — prices, news, sentiment, market data |
| **Private** | `X-API-Key` header | 21 tools — trading, balances, order management |

### Using an API Key

Set API keys in your `.env`:

```env
API_KEYS=sk-my-key-1,sk-my-key-2
```

Include in requests:

```bash
curl -X POST http://localhost:8000/api/v1/tools/place_hl_order \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-my-key-1" \
  -d '{"coin":"ETH","side":"buy","size":0.1}'
```

---

## Rate Limiting

- **Default:** 60 requests/minute per API key
- **Configurable:** Set `API_RATE_LIMIT` in `.env`
- **Header:** `X-RateLimit-Remaining` in responses

---

## Endpoints

### Meta

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API info — name, version, tool count |
| `GET` | `/health` | Health check — returns `{"status":"ok"}` |

### Tools

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/tools` | List all available tools with descriptions |
| `GET` | `/api/v1/tools/{tool_name}` | Get info + parameter schema for one tool |
| `POST` | `/api/v1/tools/{tool_name}` | **Execute a tool** — the main endpoint |

---

## Tool Reference

### 🪙 Crypto (CoinGecko) — Public

| Tool | Parameters | Returns |
|------|-----------|---------|
| `get_crypto_price` | `coin_id` (str) — e.g. "bitcoin", "ethereum" | Price, market cap, 24h change, ATH |
| `get_crypto_top_n` | `n` (int, default 10) | Top N coins by market cap |
| `search_crypto` | `query` (str) | Matching coins from CoinGecko |

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/tools/get_crypto_price \
  -H "Content-Type: application/json" \
  -d '{"coin_id":"bitcoin"}'
```

**Response:**
```json
{
  "tool": "get_crypto_price",
  "result": {
    "id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin",
    "current_price": 70617,
    "market_cap": 1412842819841,
    "price_change_pct_24h": 0.457,
    "ath": 126080
  }
}
```

---

### 🏛️ FRED Macro Data — Public

| Tool | Parameters | Returns |
|------|-----------|---------|
| `get_fred_series` | `series_id` (str) — e.g. "FEDFUNDS", "CPIAUCSL" | Latest value + metadata |
| `search_fred` | `query` (str) | Matching FRED series |
| `get_economic_dashboard` | — | GDP, CPI, unemployment, fed funds, VIX, 10Y-2Y |

**Common Series IDs:**

| ID | Metric |
|----|--------|
| `FEDFUNDS` | Federal Funds Rate |
| `CPIAUCSL` | Consumer Price Index |
| `GDP` | Gross Domestic Product |
| `UNRATE` | Unemployment Rate |
| `T10Y2Y` | 10Y-2Y Treasury Spread |
| `VIXCLS` | VIX Volatility Index |

---

### 📰 Y2 Intelligence — Public

| Tool | Parameters | Returns |
|------|-----------|---------|
| `get_news_sentiment` | `topics` (str) | Sentiment scores by topic |
| `get_news_recap` | `ticker` (str) | AI-generated news recap |
| `get_intelligence_reports` | — | Latest intelligence reports |
| `get_report_detail` | `report_id` (str) | Full report content |

---

### 🔮 Elfa AI Social — Public

| Tool | Parameters | Returns |
|------|-----------|---------|
| `get_trending_tokens` | — | Currently trending tokens from social media |
| `get_top_mentions` | `query` (str) | Most mentioned tokens matching query |
| `search_mentions` | `query` (str) | Social mention search |
| `get_trending_narratives` | — | Trending crypto narratives |
| `get_token_news` | `token` (str) | News for a specific token |

---

### 🐦 X (Twitter) — Public

| Tool | Parameters | Returns |
|------|-----------|---------|
| `search_x` | `query` (str), `max_results` (int) | Recent tweets matching query |

---

### ⚡ Hyperliquid — Mixed

| Tool | Auth | Parameters | Returns |
|------|------|-----------|---------|
| `get_hl_config` | Public | — | Connection status, wallet address |
| `get_hl_orderbook` | Public | `coin` (str), `depth` (int) | Bids, asks, mid price |
| `get_hl_account_info` | **Private** | — | Equity, margin, withdrawable |
| `get_hl_positions` | **Private** | — | Open positions with PnL |
| `get_hl_open_orders` | **Private** | — | Pending orders |
| `place_hl_order` | **Private** | `coin`, `side`, `size`, `price`, `order_type` | Order confirmation |
| `cancel_hl_order` | **Private** | `coin`, `oid` | Cancellation confirmation |
| `close_hl_position` | **Private** | `coin` | Market close confirmation |

**Example — Get Positions:**
```bash
curl -X POST http://localhost:8000/api/v1/tools/get_hl_positions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-your-key"
```

---

### 🌟 Aster DEX — Mixed

| Tool | Auth | Parameters | Returns |
|------|------|-----------|---------|
| `aster_ping` | Public | — | Connectivity check |
| `aster_ticker` | Public | `symbol` (str) | 24h price stats |
| `aster_orderbook` | Public | `symbol`, `limit` | Order book |
| `aster_klines` | Public | `symbol`, `interval`, `limit` | Candlestick data |
| `aster_funding_rate` | Public | `symbol` | Current funding rate |
| `aster_exchange_info` | Public | — | All trading pairs |
| `aster_balance` | **Private** | — | Account balance |
| `aster_positions` | **Private** | — | Open positions |
| `aster_account_info` | **Private** | — | Full account info |
| `aster_place_order` | **Private** | `symbol`, `side`, `quantity`, `order_type`, `price` | Order confirmation |
| `aster_cancel_order` | **Private** | `symbol`, `order_id` | Cancellation |
| `aster_cancel_all_orders` | **Private** | `symbol` | Cancel all |
| `aster_open_orders` | **Private** | `symbol` | Pending orders |
| `aster_set_leverage` | **Private** | `symbol`, `leverage` | Leverage confirmation |

---

### 🎲 Polymarket — Mixed

| Tool | Auth | Parameters | Returns |
|------|------|-----------|---------|
| `get_polymarket_markets` | Public | — | Active prediction markets |
| `search_polymarket` | Public | `query` (str) | Search markets |
| `get_polymarket_orderbook` | Public | `token_id` | Market order book |
| `get_polymarket_price` | Public | `token_id` | Current price |
| `get_polymarket_positions` | **Private** | — | Your open positions |
| `buy_polymarket` | **Private** | `token_id`, `amount`, `price` | Buy shares |
| `sell_polymarket` | **Private** | `token_id`, `amount`, `price` | Sell shares |
| `place_polymarket_limit` | **Private** | `token_id`, `side`, `amount`, `price` | Limit order |
| `cancel_polymarket_order` | **Private** | `order_id` | Cancel order |
| `cancel_all_polymarket_orders` | **Private** | — | Cancel all |

---

## Error Handling

All errors return JSON:

```json
{
  "detail": "Tool 'invalid_tool' not found",
  "available_tools": "/api/v1/tools"
}
```

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 401 | Missing or invalid API key |
| 404 | Tool not found |
| 422 | Invalid parameters |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Server bind address |
| `API_PORT` | `8000` | Server port |
| `API_KEYS` | — | Comma-separated API keys for auth |
| `API_RATE_LIMIT` | `60` | Requests per minute per key |

---

## Deployment

### Local Development

```bash
uv run python api_server.py
# → http://localhost:8000/docs
```

### Docker

```bash
docker build -t sentinel-api .
docker run -p 8000:8000 --env-file .env sentinel-api
```

### Google Cloud Run

```bash
./deploy.sh
# → https://hyper-sentinel-v3-xxxxx.run.app/docs
```

---

## SDKs & Integration

### Python

```python
import requests

BASE = "http://localhost:8000"

# Public tool
r = requests.post(f"{BASE}/api/v1/tools/get_crypto_price",
                   json={"coin_id": "bitcoin"})
print(r.json()["result"]["current_price"])  # 70617

# Private tool
r = requests.post(f"{BASE}/api/v1/tools/get_hl_positions",
                   headers={"X-API-Key": "sk-your-key"})
print(r.json()["result"])
```

### JavaScript

```javascript
const BASE = "http://localhost:8000";

// Public
const btc = await fetch(`${BASE}/api/v1/tools/get_crypto_price`, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({coin_id: "bitcoin"})
}).then(r => r.json());

console.log(btc.result.current_price); // 70617
```

### cURL

```bash
# List all tools
curl http://localhost:8000/api/v1/tools | python3 -m json.tool

# Get tool info
curl http://localhost:8000/api/v1/tools/get_crypto_price | python3 -m json.tool

# Execute tool
curl -X POST http://localhost:8000/api/v1/tools/get_crypto_price \
  -H "Content-Type: application/json" \
  -d '{"coin_id":"bitcoin"}'
```

---

*Sentinel API v3.0.0 · Built with FastAPI · Auto-generated Swagger at `/docs`*
