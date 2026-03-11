# 📋 Hyper-Sentinel v3 — Full Capabilities Reference

> **70+ autonomous AI tools** across real-time market surveillance, multi-venue trading, macroeconomic analysis, social sentiment intelligence, quantitative analytics (DuckDB), browser automation, computer control, and 24/7 autonomous operation — powered by multi-LLM architecture with Claude, Gemini, and Grok.

---

## 🧠 Multi-Provider LLM Architecture

Hyper-Sentinel uses an **autonomous tool-calling swarm** — LLM agents receive natural language, autonomously select which tools to invoke across 10+ live data sources, execute against APIs, coordinate decisions through NATS pub/sub, and take action with built-in guardrails.

| Provider | Model | SDK | Setup |
|----------|-------|-----|-------|
| Anthropic Claude | claude-sonnet-4-20250514 | `anthropic` | Set `ANTHROPIC_API_KEY` |
| Google Gemini | gemini-2.0-flash | `openai` (compatible) | Set `GEMINI_API_KEY` |
| xAI Grok | grok-3-mini-fast | `openai` (compatible) | Set `XAI_API_KEY` |
| Ollama (Local) | Any GGUF model | `openai` (compatible) | Run `ollama serve` |

Set **one** key in your `.env` — the agent auto-detects your provider from the key prefix. Switch models mid-session with `set provider <name>`.

---

## 🤖 3 Agent Orchestration Modes

| Mode | Framework | Agents | Coordination | Command |
|------|-----------|--------|-------------|---------|
| **Solo** | Direct | 1 MarketAgent | Single agent, all 70+ tools | `solo` |
| **Swarm** | Agno | 5 specialists | Captain routes to specialists | `swarm` |
| **Team** | Upsonic | 3 specialists | Coordinate mode + shared memory | `team` |

### Swarm Breakdown (Agno — 5 Agents)

| Agent | Role | Tools & Data Sources |
|-------|------|---------------------|
| 🎖️ **Captain** | Orchestrator — routes requests, synthesizes final response | All tools (read-only delegation) |
| 📊 **Analyst** | Market research, macro regime, sentiment analysis | CoinGecko · FRED · Y2 · Elfa · X · YFinance |
| ⚡ **Trader** | Trade execution, order management, portfolio ops | Hyperliquid · Aster DEX · Polymarket |
| 🛡️ **Risk Manager** | Position sizing, PnL monitoring, cross-venue risk | Portfolio analytics · Guardrails engine |
| 🔧 **Ops** | File management, data export, infrastructure | Filesystem · GitHub · NATS admin |

### Team Breakdown (Upsonic — 3 Agents)

| Agent | Role | Tool Categories |
|-------|------|----------------|
| 📊 **Analyst** | Research + technical analysis | `CRYPTO_TOOLS` + `MACRO_TOOLS` + `SENTIMENT_TOOLS` |
| 🛡️ **RiskManager** | Risk assessment + guardrails | `ALL_TOOLS` (full read access) |
| ⚡ **Trader** | Execution only | `TRADING_TOOLS` (write access) |

---

## 📊 All 70+ Tools

### 🪙 Cryptocurrency — CoinGecko (Tools 1–3)

| # | Tool | Description | Source | Auth |
|---|------|-------------|--------|------|
| 1 | `get_crypto_price` | Live price, market cap, volume, 24h/7d/30d changes, ATH/ATL, circulating supply | CoinGecko | ❌ Free |
| 2 | `get_crypto_top_n` | Top N cryptos ranked by market cap (up to 250) with full metrics | CoinGecko | ❌ Free |
| 3 | `search_crypto` | Fuzzy search any cryptocurrency by name, symbol, or contract address | CoinGecko | ❌ Free |

### 📈 Equities — Yahoo Finance (Tools 4–6)

| # | Tool | Description | Source | Auth |
|---|------|-------------|--------|------|
| 4 | `get_stock_quote` | Live price, volume, PE ratio, 52-week range, 50/200-day MAs | Yahoo Finance | ❌ Free |
| 5 | `get_stock_history` | Historical OHLCV with auto-computed SMA, EMA, RSI, MACD, Bollinger | Yahoo Finance | ❌ Free |
| 6 | `get_stock_info` | Company fundamentals — sector, margins, ROE, beta, dividends, FCF | Yahoo Finance | ❌ Free |

### 🏛️ Macroeconomic — FRED (Tools 7–12)

| # | Tool | Description | Source | Auth |
|---|------|-------------|--------|------|
| 7 | `get_gdp` | US GDP growth rate (quarterly, annualized) | FRED | 🔑 Free key |
| 8 | `get_cpi` | Consumer Price Index — inflation tracking | FRED | 🔑 Free key |
| 9 | `get_interest_rates` | Federal funds rate, prime rate, treasury yields | FRED | 🔑 Free key |
| 10 | `get_yield_curve` | 2Y/10Y spread — recession indicator | FRED | 🔑 Free key |
| 11 | `get_vix` | CBOE Volatility Index — fear gauge | FRED | 🔑 Free key |
| 12 | `get_unemployment` | US unemployment rate + labor market data | FRED | 🔑 Free key |

### 📰 News & Intelligence — Y2 / GloriaAI (Tools 13–15)

| # | Tool | Description | Source | Auth |
|---|------|-------------|--------|------|
| 13 | `get_y2_news` | Curated financial news with AI-scored sentiment | Y2 Intelligence | 🔑 API key |
| 14 | `get_y2_recap` | Daily market recap with key events + market movers | Y2 Intelligence | 🔑 API key |
| 15 | `get_y2_report` | Deep-dive research report on any topic or asset | GloriaAI | 🔑 API key |

### 🐦 Social Sentiment — Elfa AI + X/Twitter (Tools 16–20)

| # | Tool | Description | Source | Auth |
|---|------|-------------|--------|------|
| 16 | `get_trending_tokens` | Trending tokens by social volume with momentum scores | Elfa AI | 🔑 API key |
| 17 | `get_token_mentions` | Social mention count + sentiment for any token | Elfa AI | 🔑 API key |
| 18 | `get_elfa_top_mentions` | Top mentioned tokens across all tracked platforms | Elfa AI | 🔑 API key |
| 19 | `search_x_posts` | Search X/Twitter for posts about any topic or ticker | X API | 🔑 Bearer |
| 20 | `get_x_sentiment` | Aggregated sentiment analysis from X posts | X API | 🔑 Bearer |

### ⚡ Trading — Hyperliquid (Tools 21–27)

| # | Tool | Description | Source | Auth |
|---|------|-------------|--------|------|
| 21 | `get_hl_account` | Account overview — balances, equity, margin, PnL | Hyperliquid | 🔐 Wallet |
| 22 | `get_hl_positions` | All open positions with entry, size, liquidation price | Hyperliquid | 🔐 Wallet |
| 23 | `get_hl_orderbook` | Level 2 orderbook for any trading pair | Hyperliquid | ❌ Free |
| 24 | `place_hl_order` | Place limit/market orders with leverage up to 50x | Hyperliquid | 🔐 Wallet |
| 25 | `cancel_hl_order` | Cancel open orders by ID or pair | Hyperliquid | 🔐 Wallet |
| 26 | `get_hl_funding` | Current funding rates across all pairs | Hyperliquid | ❌ Free |
| 27 | `get_hl_trades` | Recent trade history with timestamps | Hyperliquid | 🔐 Wallet |

### 🌟 Trading — Aster DEX (Tools 28–34)

| # | Tool | Description | Source | Auth |
|---|------|-------------|--------|------|
| 28 | `get_aster_account` | Account balances and trading status | Aster DEX | 🔑 API key |
| 29 | `get_aster_positions` | Open positions with PnL, leverage, margin | Aster DEX | 🔑 API key |
| 30 | `place_aster_order` | Place limit/market orders on Aster futures | Aster DEX | 🔑 API key |
| 31 | `get_aster_klines` | OHLCV candlestick data for any timeframe | Aster DEX | 🔑 API key |
| 32 | `get_aster_funding` | Current funding rates for all Aster pairs | Aster DEX | 🔑 API key |
| 33 | `get_aster_orderbook` | Level 2 orderbook depth | Aster DEX | 🔑 API key |
| 34 | `get_aster_ticker` | 24h ticker with volume and price change | Aster DEX | 🔑 API key |

### 🔮 Prediction Markets — Polymarket (Tools 35–38)

| # | Tool | Description | Source | Auth |
|---|------|-------------|--------|------|
| 35 | `get_polymarket_markets` | Active prediction markets with probabilities and volume | Polymarket | ❌ Free |
| 36 | `get_polymarket_market` | Detailed view of a specific market with full order data | Polymarket | ❌ Free |
| 37 | `place_poly_order` | Place buy/sell orders on prediction outcomes | Polymarket | 🔑 API key |
| 38 | `get_poly_positions` | Current prediction market positions and PnL | Polymarket | 🔑 API key |

### 📉 Technical Analysis Engine (Tools 39–43)

| # | Tool | Description | Method |
|---|------|-------------|--------|
| 39 | `compute_sma` | Simple Moving Average (configurable window) | `pandas` rolling mean |
| 40 | `compute_rsi` | Relative Strength Index (14-period default) | Wilder's smoothing |
| 41 | `compute_macd` | MACD line, signal line, histogram | EMA(12) − EMA(26), signal EMA(9) |
| 42 | `compute_bollinger` | Bollinger Bands — upper, middle, lower | SMA(20) ± 2σ |
| 43 | `sma_crossover` | Golden cross / death cross detection | SMA(50) vs SMA(200) |

### 🛡️ Guardrails & Safety (Tools 44–48)

| # | Tool | Description | Default |
|---|------|-------------|---------|
| 44 | `check_trade_limit` | Validates trade size against max | $100 per trade |
| 45 | `check_daily_count` | Enforces maximum daily trade count | 5 trades/day |
| 46 | `check_daily_loss` | Halts trading if daily loss exceeded | $250 max loss |
| 47 | `kill_switch` | Emergency halt — cancels all pending, freezes execution | Manual trigger |
| 48 | `guardrails_status` | Dashboard of all active limits and usage | `guardrails` command |

### 🌐 Browser Automation — 3-Tier System (Tools 49–51)

| # | Tool | Tier | Description | Tech |
|---|------|------|-------------|------|
| 49 | `open_in_browser` | **Tier 1** | Instant Chrome tab — `open youtube`, `open tradingview` | `webbrowser` stdlib |
| 50 | `browse_task` | **Tier 2** | LLM-driven browser automation — "find SOL price on CoinMarketCap" | `browser-use` + Playwright |
| 51 | `computer_use_task` | **Tier 3** | Full computer control — launch apps, type, interact | Anthropic Computer Use |

### 🖥️ Computer Control (Tools 52–57)

| # | Tool | Description | Scope |
|---|------|-------------|-------|
| 52 | `launch_app` | Open any macOS application by name | `open -a <app>` |
| 53 | `get_system_info` | CPU, memory, disk, uptime, network stats | `psutil` |
| 54 | `run_shell` | Execute shell commands (sandboxed, logged) | Allowlisted commands |
| 55 | `screenshot` | Capture screen for visual analysis | `screencapture` |
| 56 | `type_text` | Type text into the active application | AppleScript |
| 57 | `clipboard_ops` | Read/write system clipboard | `pbcopy` / `pbpaste` |

### 📊 EODHD Historical Data (Tools 58–60)

| # | Tool | Description | Source | Auth |
|---|------|-------------|--------|------|
| 58 | `get_eod_history` | End-of-day OHLCV data for any instrument (150K+ symbols globally) | EODHD | 🔑 API key |
| 59 | `get_eod_fundamentals` | Company fundamentals — financials, valuations, dividends, insider trades | EODHD | 🔑 API key |
| 60 | `get_eod_intraday` | Intraday OHLCV data (1m, 5m, 1h intervals) for real-time analysis | EODHD | 🔑 API key |

### 🦆 DuckDB SQL Analytics Engine (Tools 61–70)

All quantitative analysis runs as **pure SQL inside DuckDB** — embedded columnar database with zero-copy Arrow ingestion. No external database server required.

| # | Tool | Description | SQL Technique |
|---|------|-------------|---------------|
| 61 | `daily_returns` | Day-over-day percentage change | `LAG()` window function |
| 62 | `moving_averages` | 50-day and 200-day simple moving averages | `AVG() OVER (ROWS BETWEEN)` |
| 63 | `bollinger_bands` | ±2σ bands around 50-day MA | `STDDEV_POP() OVER ()` + CTE |
| 64 | `cross_signals` | Golden Cross / Death Cross detection | `LAG()` + `CASE WHEN` |
| 65 | `rolling_volatility` | 30-day rolling annualized volatility | `STDDEV_POP()` + `SQRT(252)` |
| 66 | `max_drawdown` | Peak-to-trough drawdown percentage | `MAX() OVER (UNBOUNDED)` |
| 67 | `monthly_returns` | Month-over-month returns | 3 chained CTEs + self-JOIN |
| 68 | `yearly_returns` | Year-over-year returns | CTEs + `LAG()` |
| 69 | `backtest_ma_crossover` | MA crossover strategy equity curve | `EXP(SUM(LN()))` cumulative |
| 70 | `buy_and_hold` | Passive benchmark equity curve | `EXP(SUM(LN()))` cumulative |

---

## 🛡️ Autonomous Runtime — Sentinel Mode

The Sentinel runtime operates 24/7 with **zero human intervention** once started.

### Monitor Loop

| Monitor | Interval | Data Source | Trigger |
|---------|----------|-------------|---------|
| **Price Monitor** | 15 min | CoinGecko + Hyperliquid | Threshold breach (±5% default) |
| **Position Monitor** | 30 min | Hyperliquid + Aster | Drawdown > 10%, leverage warning |
| **Sentiment Monitor** | 60 min | Y2 + Elfa + X | Social volume spike detection |
| **Macro Monitor** | 6 hours | FRED | Regime change (CPI, rates, VIX) |

### Decision Pipeline

```
Monitor Alert → Team Analysis → Risk Check → Guardrail Validation → Execute / Escalate
                                                    ↓
                                              Decision Log (SQLite)
                                              Telegram Notification
                                              NATS Event Broadcast
```

### Mission Templates

| Mission | Trigger | Behavior |
|---------|---------|----------|
| **Trail Stop** | Price move | Trailing stop-loss at configurable % |
| **Scheduled Briefing** | Cron schedule | Morning/evening market briefing |
| **Sentiment Alert** | Social spike | Alert when token sentiment flips |
| **DCA** | Cron schedule | Recurring buy at fixed USD amount |
| **Portfolio Rebalance** | Drift threshold | Auto-rebalance when allocation drifts |

---

## 📡 NATS JetStream — Event-Driven Architecture

All agent communication flows through NATS subjects:

| Subject | Publisher | Subscriber | Payload |
|---------|-----------|------------|---------|
| `sentinel.market.data` | Monitors | MarketAgent | Price/sentiment snapshots |
| `sentinel.risk.input` | MarketAgent | RiskManager | Trade proposals |
| `sentinel.risk.output` | RiskManager | Trader | Approved/rejected decisions |
| `sentinel.alerts.*` | Any | Telegram + Logs | Alert notifications |
| `sentinel.missions.*` | Scheduler | Sentinel | Mission triggers |

---

## 🔌 Data Sources

| Source | Coverage | Auth | Rate Limits |
|--------|----------|------|-------------|
| **CoinGecko** | 10,000+ cryptocurrencies | ❌ Free | 10–30 req/min |
| **Yahoo Finance** | All NYSE/NASDAQ equities + options | ❌ Free | ~2,000 req/hr |
| **Polymarket** | Active prediction markets | ❌ Free (browse) | Public API |
| **FRED** | 800,000+ economic time series | 🔑 Free key | 120 req/min |
| **EODHD** | 150,000+ instruments globally (EOD + intraday + fundamentals) | 🔑 API key | Per-plan |
| **Y2 Intelligence** | AI-curated financial news + analysis | 🔑 API key | Per-plan |
| **Elfa AI** | Social sentiment + trending tokens | 🔑 API key | Per-plan |
| **X / Twitter** | Real-time social posts + sentiment | 🔑 Bearer | Per-plan |
| **Hyperliquid** | Perpetual futures + orderbook | 🔐 Wallet | No limit |
| **Aster DEX** | Futures, leverage, funding | 🔑 API key | Per-plan |
| **DuckDB** | Embedded columnar analytics (local, zero config) | ❌ Built-in | Unlimited |

> **3 sources are completely free** (CoinGecko, Yahoo Finance, Polymarket). FRED and EODHD require free API keys. DuckDB runs locally. The rest are optional premium integrations.

---

## 🌐 REST API Server

Every tool is exposed as an HTTP endpoint via `api_server.py` — a FastAPI server with auto-generated Swagger documentation.

### Endpoints

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | API info, tool count, version |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI (interactive) |
| `/redoc` | GET | ReDoc (alternative docs) |
| `/api/v1/tools` | GET | List all tools with schemas |
| `/api/v1/tools/{name}` | GET | Tool info + usage example |
| `/api/v1/tools/{name}` | POST | Execute a tool |

### Auth Tiers

| Tier | Tools | Auth |
|------|-------|------|
| **Public** | Crypto prices, FRED, news, Elfa, Aster market data, Polymarket browse | None required |
| **Private** | HL trading, Aster orders, Polymarket trades, account info | `X-API-Key` header |

### Setup

```bash
# 1. Add API keys to .env (optional — without this, all tools are open)
echo 'API_KEYS=sk-your-key-here' >> .env

# 2. Start the API server
uv run python api_server.py

# 3. Open Swagger docs
open http://localhost:8000/docs
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEYS` | *(empty = dev mode)* | Comma-separated API keys for auth |
| `API_PORT` | `8000` | Server port |
| `API_HOST` | `0.0.0.0` | Bind address |
| `API_RATE_LIMIT` | `60` | Requests per minute per key |

---

## 📦 Core Dependencies

| Package | Purpose |
|---------|---------|
| `anthropic` | Claude API (primary LLM) |
| `openai` | GPT-4 / Gemini / Grok (multi-provider via compatible SDK) |
| `upsonic` | Agent framework — Teams, Memory, Safety Engine, @tool |
| `agno` | Swarm orchestration — 5-agent coordinate mode |
| `duckdb` | Embedded columnar analytics database (SQL engine) |
| `pyarrow` | Zero-copy data ingestion for DuckDB |
| `browser-use` | Tier 2 LLM-driven browser automation |
| `playwright` | Browser engine for Tier 2 |
| `langchain-anthropic` | LangChain adapter for browser-use |
| `nats-py` | NATS.io + JetStream client |
| `rich` | Terminal UI — tables, panels, progress |
| `pandas` + `numpy` | Data manipulation + quantitative analysis |
| `pandas-ta` | Technical analysis indicators (70+) |
| `matplotlib` | Publication-quality financial charts |
| `requests` | HTTP client for all API integrations |
| `python-dotenv` | Environment variable management |
| `pydantic` | Data validation + serialization |
| `schedule` | Cron-style task scheduling |
| `hyperliquid-python-sdk` | Hyperliquid DEX trading |
| `fastapi` | REST API server framework (auto-generated endpoints) |
| `uvicorn` | ASGI server for FastAPI |

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                   HYPER-SENTINEL v3 RUNTIME                   │
│                                                              │
│  ┌─── LLM LAYER ──────────────────────────────────────────┐ │
│  │  Claude · Gemini · Grok · Ollama (auto-detect)         │ │
│  └────────────────────────────────────────────────────────┘ │
│                          ↕ tool calls                        │
│  ┌─── AGENT LAYER ────────────────────────────────────────┐ │
│  │  Solo (1) · Swarm (5 Agno) · Team (3 Upsonic)         │ │
│  │  70+ tools · Shared memory · Safety policies           │ │
│  └────────────────────────────────────────────────────────┘ │
│                          ↕ NATS pub/sub                      │
│  ┌─── DATA LAYER ─────────────────────────────────────────┐ │
│  │  CoinGecko · YFinance · FRED · EODHD · Y2 · Elfa · X  │ │
│  │  Hyperliquid · Aster · Polymarket · DuckDB (local)     │ │
│  └────────────────────────────────────────────────────────┘ │
│                          ↕ events                            │
│  ┌─── AUTONOMOUS LAYER ──────────────────────────────────┐ │
│  │  4 Monitors · 5 Mission types · Guardrails · Kill SW   │ │
│  │  Decision logging · Telegram alerts · Memory           │ │
│  └────────────────────────────────────────────────────────┘ │
│                          ↕ execution                         │
│  ┌─── BROWSER + COMPUTER CONTROL ────────────────────────┐ │
│  │  Tier 1: Chrome direct · Tier 2: Playwright + LLM     │ │
│  │  Tier 3: Computer Use · Docker shell isolation         │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

**Built by the [Hyper Sentinel](https://github.com/hyper-sentinel) team · 6th Generation · March 2026**
