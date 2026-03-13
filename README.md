<h1 align="center">🛡️ Hyper-Sentinel</h1>

<p align="center">
<strong>Autonomous AI Agent Swarm for Financial Surveillance, Trading & Market Intelligence</strong>
</p>

<p align="center">
Crypto · Equities · Options · Prediction Markets · Macro · Sentiment · Browser Automation
</p>

<p align="center">
<img src="https://img.shields.io/badge/PYTHON-3.13+-blue?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/AI-AUTONOMOUS-blueviolet?style=for-the-badge" />
<img src="https://img.shields.io/badge/CLAUDE · GEMINI · GROK-LLM-green?style=for-the-badge" />
<img src="https://img.shields.io/badge/TOOLS-70+-orange?style=for-the-badge" />
<img src="https://img.shields.io/badge/REST_API-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/LICENSE-PROPRIETARY-red?style=for-the-badge" />
</p>

<p align="center">
<img src="https://img.shields.io/badge/data-CoinGecko-yellow" />
<img src="https://img.shields.io/badge/data-Yahoo%20Finance-purple" />
<img src="https://img.shields.io/badge/data-FRED-blue" />
<img src="https://img.shields.io/badge/data-Polymarket-green" />
<img src="https://img.shields.io/badge/data-Hyperliquid-cyan" />
<img src="https://img.shields.io/badge/data-Aster%20DEX-orange" />
<img src="https://img.shields.io/badge/data-EODHD-teal" />
<img src="https://img.shields.io/badge/data-Elfa%20AI-pink" />
<img src="https://img.shields.io/badge/data-X%20%2F%20Twitter-black" />
<img src="https://img.shields.io/badge/data-Y2%20Intel-red" />
</p>

---

## 📦 Overview

Hyper-Sentinel is an **autonomous AI agent swarm** that conducts 24/7 financial surveillance, executes trades across multiple DEXs, runs SQL-native quantitative analysis via DuckDB, and controls your computer through natural language — powered by your choice of LLM provider.

> 📋 [**Full Capabilities Reference →**](CAPABILITIES.md) — detailed breakdown of all 70+ tools, agent modes, data sources, and architecture.

> 🏗️ [**Architecture & Trading Setup →**](ARCHITECTURE.md) — system design + Hyperliquid, Aster, Polymarket, EODHD setup guides.

**3 free data sources. No API keys required for market data.** You only need one LLM provider key.

---

## 🚀 Getting Started

### Step 1 · Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2 · Install Docker

Download [Docker Desktop](https://www.docker.com/products/docker-desktop/) or:

```bash
brew install --cask docker
```

### Step 3 · Clone & run

```bash
git clone https://github.com/hyper-sentinel/hyper-sentinel.git
cd hyper-sentinel
```

### Step 4 · One command

```bash
docker compose up -d nats && uv run main.py
```

**That's it.** One line boots everything:
- 🖥️ **Interactive REPL** — chat with the AI agent
- 🌐 **REST API** — auto-starts on `http://localhost:8000/docs` (49 tools)
- 📡 **NATS messaging** — pub/sub event fabric

On first run, the interactive setup walks you through configuration — paste any supported AI provider key and you're live. All keys are auto-saved to `.env`.

### Step 5 · Go autonomous

Once the REPL is running, type `sentinel` to start the 24/7 monitoring loop:

```
⚡ You → sentinel
```

This activates 4 monitors (price, positions, sentiment, macro) that run on intervals, detect threshold breaches, and trigger the agent team to analyze and act.

---

## ⚡ Capabilities

| Domain | Tools | Source |
|--------|-------|--------|
| **Crypto** | `get_crypto_price` · `get_crypto_top_n` · `search_crypto` | CoinGecko |
| **Equities** | `get_stock_quote` · `get_stock_history` · `get_stock_info` | Yahoo Finance |
| **Macro** | `get_gdp` · `get_cpi` · `get_interest_rates` · `get_vix` · `get_yield_curve` | FRED |
| **News & Intel** | `get_y2_news` · `get_y2_recap` · `get_y2_report` | Y2 / GloriaAI |
| **Social Sentiment** | `get_trending_tokens` · `get_token_mentions` · `search_x_posts` | Elfa AI · X |
| **Trading (HL)** | `get_hl_account` · `place_hl_order` · `get_hl_positions` + 4 more | Hyperliquid |
| **Trading (Aster)** | `get_aster_account` · `place_aster_order` · `get_aster_klines` + 4 more | Aster DEX |
| **Prediction Mkts** | `get_polymarket_markets` · `place_poly_order` + 2 more | Polymarket |
| **Technical Analysis** | `compute_sma` · `compute_rsi` · `compute_macd` · `compute_bollinger` | Built-in |
| **Quant Analytics** | `daily_returns` · `bollinger_bands` · `rolling_volatility` · `max_drawdown` + 6 more | DuckDB SQL |
| **EODHD Data** | `get_eod_history` · `get_eod_fundamentals` · `get_eod_intraday` | EODHD |
| **Browser (3-Tier)** | `open_in_browser` · `browse_task` · `computer_use_task` | Chrome · Playwright · Anthropic |
| **Computer Control** | `launch_app` · `run_shell` · `screenshot` · `type_text` + 2 more | macOS native |
| **Guardrails** | `check_trade_limit` · `kill_switch` · `guardrails_status` + 2 more | Built-in |

---

## 🌐 REST API

The REST API **starts automatically** when you run `uv run main.py` — no separate terminal needed. All 49+ tools are exposed as HTTP endpoints with Swagger docs.

```
📡 Infrastructure
  🌐 REST API    ● http://localhost:8000/docs    49 tools
```

| Feature | Details |
|---------|---------|
| **Endpoints** | `POST /api/v1/tools/{tool_name}` — one endpoint per tool |
| **Auth** | `X-API-Key` header for trading tools; public tools (prices, news) require no auth |
| **Rate Limit** | 60 req/min per key (configurable via `API_RATE_LIMIT`) |
| **Docs** | Auto-generated Swagger at `/docs`, ReDoc at `/redoc` |
| **SaaS Keys** | `add api` in terminal to configure auth keys |
| **Disable** | Set `API_ENABLED=false` in `.env` to turn off |


**Quick test (no auth needed):**
```bash
curl http://localhost:8000/api/v1/tools/get_crypto_price \
  -X POST -H "Content-Type: application/json" \
  -d '{"coin_id": "bitcoin"}'
```

**Authenticated (trading):**
```bash
curl http://localhost:8000/api/v1/tools/place_hl_order \
  -X POST -H "Content-Type: application/json" \
  -H "X-API-Key: sk-your-key" \
  -d '{"coin": "ETH", "side": "buy", "size": 0.1}'
```

> Set `API_KEYS=sk-key1,sk-key2` in `.env` to enable auth. Without it, all tools are open (dev mode).

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Agent Frameworks** | Upsonic (Teams, Memory, Safety Engine) + Agno (swarm) |
| **LLM Providers** | Claude · Gemini · Grok · Ollama (auto-detect from key prefix) |
| **Browser Automation** | Tier 1: Chrome direct · Tier 2: browser-use + Playwright · Tier 3: Computer Use |
| **Message Fabric** | NATS.io + JetStream |
| **Trading** | Hyperliquid SDK + Aster DEX + Polymarket CLOB |
| **Data** | CoinGecko · FRED · EODHD · Y2 · Elfa AI · X · YFinance |
| **Analytics** | DuckDB (embedded columnar) + PyArrow (zero-copy) |
| **Notifications** | Telegram (bot + client) |
| **Terminal UI** | Rich |
| **Deploy** | Docker Compose → Cloud Run |
| **REST API** | FastAPI + Uvicorn — auto-generated Swagger at `/docs` |

---

## 🤖 3 Agent Modes

| Mode | Command | What Happens |
|------|---------|-------------|
| **Solo** | `solo` | Single MarketAgent has all 70+ tools directly |
| **Swarm** | `swarm` | 5 Agno agents coordinate — Captain routes to specialists |
| **Team** | `team` | 3 Upsonic agents in coordinate mode with shared memory |

### Swarm Agents (Agno)

| Agent | Role | Specialty |
|-------|------|-----------|
| 🎖️ **Captain** | Routes requests, synthesizes | Orchestrator |
| 📊 **Analyst** | Market research, macro, sentiment | CoinGecko, FRED, Y2, X |
| ⚡ **Trader** | Trade execution | Hyperliquid, Aster, Polymarket |
| 🛡️ **Risk Manager** | Position sizing, PnL, risk | Cross-venue portfolio |
| 🔧 **Ops** | File management, data export | Filesystem, GitHub |

### Team Agents (Upsonic)

Upsonic provides **coordinate mode** — agents share memory, enforce safety policies, and hand off tasks in sequence. Built-in Safety Engine validates every action before execution.

| Agent | Role | Tool Categories | Upsonic Features |
|-------|------|----------------|-----------------|
| 📊 **Analyst** | Research + technical analysis | `CRYPTO_TOOLS` + `MACRO_TOOLS` + `SENTIMENT_TOOLS` | Shared memory, @tool wrappers |
| 🛡️ **RiskManager** | Risk assessment + guardrails | `ALL_TOOLS` (full read access) | Safety Engine, PII anonymization |
| ⚡ **Trader** | Execution only | `TRADING_TOOLS` (write access) | Approval-gated, audit logged |

**Upsonic Key Capabilities:**
- 🧠 **Shared Memory** — agents persist context across tasks via SQLite-backed memory
- 🛡️ **Safety Engine** — `PIIAnonymizePolicy` + `FinancialDataPolicy` enforce compliance
- 🔧 **@tool Wrappers** — 20 scraper functions decorated as Upsonic tools (zero MCP overhead)
- 📋 **Coordinate Mode** — Analyst → RiskManager → Trader pipeline with handoff

---

## 🛡️ Autonomous Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   HYPER-SENTINEL RUNTIME                   │
│                                                              │
│  ┌─── MONITORS ──────────────────────────────────────────┐  │
│  │ Price (15m) · Positions (30m) · Sentiment (60m)       │  │
│  │ Macro (6h) — threshold-based, zero LLM cost          │  │
│  └───────────────────────────────────────────────────────┘  │
│                       ↓ threshold breach                     │
│  ┌─── AGENT TEAM ────────────────────────────────────────┐  │
│  │ Analyst → RiskManager → Trader                        │  │
│  │ 70+ tools · 11+ data sources · 20 @tool scrapers     │  │
│  └───────────────────────────────────────────────────────┘  │
│                       ↓ decision                             │
│  ┌─── GUARDRAILS ────────────────────────────────────────┐  │
│  │ Max: $100/trade · 5/day · $250 loss limit · Kill SW   │  │
│  └───────────────────────────────────────────────────────┘  │
│                       ↓ execute / escalate                   │
│  ┌─── OUTPUT ────────────────────────────────────────────┐  │
│  │ Telegram · NATS broadcast · Decision log · Memory     │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Guardrails

| Guardrail | Default | Env Var |
|-----------|---------|---------|
| Max trade size | $100 | `SENTINEL_MAX_TRADE_USD` |
| Max daily trades | 5 | `SENTINEL_MAX_DAILY_TRADES` |
| Max daily loss | $250 | `SENTINEL_MAX_DAILY_LOSS` |
| Auto-execute | Off | `SENTINEL_AUTO_EXECUTE` |
| Kill switch | Manual | In-code emergency halt |

---

## 📡 4 Monitors

| Monitor | Interval | What It Watches |
|---------|----------|----------------|
| **Price** | 15 min | Threshold alerts on any tracked asset |
| **Position** | 30 min | Drawdown, leverage, PnL warnings |
| **Sentiment** | 60 min | Y2/Elfa/X social spike detection |
| **Macro** | 6 hours | FRED regime changes (CPI, rates, VIX) |

---

## 🎯 3 Mission Templates

| Mission | Trigger | Example |
|---------|---------|---------|
| **Trail Stop** | Price move | "Trail BTC with 3% stop" |
| **Briefing** | Schedule | "Morning crypto briefing at 8am" |
| **Alert** | Sentiment | "Alert if SOL sentiment flips negative" |


---

## Commands

| Command | What It Does |
|---|---|
| *any question* | Ask the active agent anything |
| `solo` | Single MarketAgent (default) |
| `swarm` | Agno 5-agent team |
| `team` | Upsonic Team (coordinate mode) |
| `sentinel` | Start autonomous 24/7 loop |
| `sentinel stop` | Stop the loop |
| `guardrails` | Show trade limits + kill switch |
| `mission list` | Show standing orders |
| `mission add <desc>` | Create a new mission |
| `scan <symbols>` | Publish market scan to NATS |
| `open <site>` | Tier 1: Instant Chrome open (youtube, tradingview, etc.) |
| `browse <task>` | Tier 2: LLM + Playwright browser automation (complex tasks) |
| `add` | Show available data source integrations |
| `add <service>` | Configure API key (hl, y2, elfa, fred, etc.) |
| `status` | Infrastructure dashboard |
| `logs [N]` | Last N decisions |
| `help` | All commands |
| `quit` | Shutdown |

---

## 📁 Project Structure

```
hyper-sentinel/
├── main.py                  # Entry point — REPL + command routing
├── core/                    # Runtime engine
│   ├── sentinel.py          # Autonomous 24/7 loop
│   ├── monitors.py          # 4 watchers (price, position, sentiment, macro)
│   ├── missions.py          # Standing orders system
│   ├── tools.py             # 70+ Upsonic @tool wrappers
│   ├── tool_registry.py     # Unified registration + schema generation
│   ├── ta_engine.py         # Technical analysis (SMA, RSI, MACD, Bollinger)
│   ├── strategy_runner.py   # SMA crossover auto-trading
│   ├── memory.py            # Persistent state
│   └── scheduler.py         # Cron-style task scheduler
├── api/                     # HTTP layer
│   ├── server.py            # REST API (FastAPI) — auto-starts on :8000
│   ├── webhook.py           # TradingView webhook receiver
│   └── trading_mcp.py       # MCP trading server
├── automation/              # Computer + browser control
│   ├── browser.py           # 3-tier (Chrome → Playwright → Computer Use)
│   ├── computer.py          # macOS native control
│   └── telegram.py          # Telegram Client API
├── agents/                  # Multi-agent orchestration
│   ├── market-agent/        # Upsonic solo agent
│   ├── swarm.py             # Agno 5-agent team
│   ├── team.py              # Upsonic coordinate mode
│   ├── analyst.py           # Research specialist
│   ├── trader.py            # Execution specialist
│   └── risk_manager.py      # Risk specialist
├── scrapers/                # 8 data connectors
│   ├── crypto_scraper.py    # CoinGecko
│   ├── fred_scraper.py      # FRED macro
│   ├── y2_scraper.py        # Y2 Intelligence
│   ├── elfa_scraper.py      # Elfa AI social
│   ├── x_scraper.py         # X / Twitter
│   ├── hyperliquid_scraper.py
│   ├── aster_scraper.py
│   └── polymarket_scraper.py
├── docker/                  # Container config
│   ├── docker-compose.yml
│   └── nats-server.conf
├── docs/                    # Reference documentation
└── pyproject.toml
```

---

## License

Copyright © 2026 Morgan Fisher. All rights reserved. Viewing only — see [LICENSE](LICENSE).

---

<p align="center"><strong>Built by <a href="https://github.com/hyper-sentinel">Hyper Sentinel</a> · March 2026</strong></p>
