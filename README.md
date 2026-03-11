<h1 align="center">🛡️ Hyper-Sentinel v3</h1>

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
<img src="https://img.shields.io/badge/TOOLS-57+-orange?style=for-the-badge" />
<img src="https://img.shields.io/badge/LICENSE-PROPRIETARY-red?style=for-the-badge" />
</p>

<p align="center">
<img src="https://img.shields.io/badge/data-CoinGecko-yellow" />
<img src="https://img.shields.io/badge/data-Yahoo%20Finance-purple" />
<img src="https://img.shields.io/badge/data-FRED-blue" />
<img src="https://img.shields.io/badge/data-Polymarket-green" />
<img src="https://img.shields.io/badge/data-Hyperliquid-cyan" />
<img src="https://img.shields.io/badge/data-Aster%20DEX-orange" />
<img src="https://img.shields.io/badge/data-Elfa%20AI-pink" />
<img src="https://img.shields.io/badge/data-X%20%2F%20Twitter-black" />
<img src="https://img.shields.io/badge/data-Y2%20Intel-red" />
</p>

---

## 📦 Overview

Hyper-Sentinel v3 is an **autonomous AI agent swarm** that conducts 24/7 financial surveillance, executes trades across multiple DEXs, and controls your computer through natural language — powered by your choice of LLM provider.

> 📋 [**Full Capabilities Reference →**](CAPABILITIES.md) — detailed breakdown of all 57+ tools, agent modes, data sources, and architecture.

**3 free data sources. No API keys required for market data.** You only need one LLM provider key.

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
| **Browser (3-Tier)** | `open_in_browser` · `browse_task` · `computer_use_task` | Chrome · Playwright · Anthropic |
| **Computer Control** | `launch_app` · `run_shell` · `screenshot` · `type_text` + 2 more | macOS native |
| **Guardrails** | `check_trade_limit` · `kill_switch` · `guardrails_status` + 2 more | Built-in |

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

### Step 3 · Run it

```bash
git clone https://github.com/hyper-sentinel/hyper-sentinel-v3.git && cd hyper-sentinel-v3 && docker compose up -d nats && uv run main.py
```

**That's it.** On first run, the interactive setup walks you through configuration — paste any supported AI provider key and you're live. All keys are auto-saved to `.env`.

### Step 4 · Go autonomous

Once configured, start the autonomous monitoring loop:

```
⚡ You → sentinel
🛡️ Sentinel autonomous loop started!
```

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Agent Frameworks** | Upsonic (Teams, Memory, Safety Engine) + Agno (swarm) |
| **LLM Providers** | Claude · Gemini · Grok · Ollama (auto-detect from key prefix) |
| **Browser Automation** | Tier 1: Chrome direct · Tier 2: browser-use + Playwright · Tier 3: Computer Use |
| **Message Fabric** | NATS.io + JetStream |
| **Trading** | Hyperliquid SDK + Aster DEX + Polymarket CLOB |
| **Data** | CoinGecko · FRED · Y2 · Elfa AI · X · YFinance |
| **Storage** | SQLite (Upsonic Memory + decision logs) → Postgres |
| **Notifications** | Telegram (bot + client) |
| **Terminal UI** | Rich |
| **Deploy** | Docker Compose → Cloud Run |

---

## 🤖 3 Agent Modes

| Mode | Command | What Happens |
|------|---------|-------------|
| **Solo** | `solo` | Single MarketAgent has all 57+ tools directly |
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

---

## 🛡️ Autonomous Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   HYPER-SENTINEL v3 RUNTIME                   │
│                                                              │
│  ┌─── MONITORS ──────────────────────────────────────────┐  │
│  │ Price (15m) · Positions (30m) · Sentiment (60m)       │  │
│  │ Macro (6h) — threshold-based, zero LLM cost          │  │
│  └───────────────────────────────────────────────────────┘  │
│                       ↓ threshold breach                     │
│  ┌─── AGENT TEAM ────────────────────────────────────────┐  │
│  │ Analyst → RiskManager → Trader                        │  │
│  │ 57+ tools · 10+ data sources · 20 @tool scrapers     │  │
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

## 🎯 5 Mission Templates

| Mission | Trigger | Example |
|---------|---------|---------|
| **Trail Stop** | Price move | "Trail BTC with 3% stop" |
| **Briefing** | Schedule | "Morning crypto briefing at 8am" |
| **Alert** | Sentiment | "Alert if SOL sentiment flips negative" |
| **DCA** | Schedule | "Buy $50 BTC every Monday" |
| **Rebalance** | Drift | "Rebalance portfolio if >5% drift" |

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

## Generation Lineage

| Gen | Project | Key Upgrade |
|-----|---------|-------------|
| 1st | `fintech-terminal` | Single agent, foundation |
| 2nd | `agentic-fintech-terminal` | 5-agent swarm, 7 MCP servers |
| 3rd | `agentic-hyper-terminal` | Dual-DEX, FRED macro, browser automation |
| 4th | `agentic-hyper-sentinel` | Autonomous 24/7, monitors, missions, guardrails |
| 5th | `hyper-sentinel-v2` | NATS pub/sub, Upsonic Teams, @tool scrapers, coordinate mode |
| **6th** | **`hyper-sentinel-v3`** | **3-tier browser automation, multi-LLM, Docker shell isolation** |

---

## 📁 Project Structure

```
hyper-sentinel-v3/
├── main.py                  # Interactive REPL + command routing
├── sentinel.py              # Autonomous runtime loop
├── browser_agent.py         # 3-tier browser (Tier 1: Chrome → Tier 2: Playwright → Tier 3: Computer Use)
├── computer_use.py          # Safe computer control (apps, system info, shell)
├── tools.py                 # 20 Upsonic @tool wrappers
├── tool_registry.py         # Unified tool registration
├── monitors.py              # 4 continuous watchers
├── missions.py              # Standing orders system
├── memory.py                # Persistent state (SQLite → Postgres)
├── scheduler.py             # Cron-style task scheduler
├── strategy_runner.py       # SMA crossover auto-trading
├── ta_engine.py             # Technical analysis (pandas-ta)
├── telegram_client.py       # Telegram notifications
├── swarm.py                 # Agno 5-agent team
├── team.py                  # Upsonic Team (coordinate mode)
├── trading_mcp.py           # MCP trading server
├── webhook_server.py        # TradingView webhook receiver
├── agents/
│   ├── market-agent/        # Upsonic Agent + YFinanceTools
│   ├── analyst.py           # Research specialist
│   ├── trader.py            # Execution specialist
│   └── risk_manager.py      # Risk specialist
├── scrapers/                # 8 data modules
│   ├── crypto_scraper.py    # CoinGecko
│   ├── fred_scraper.py      # FRED macro
│   ├── y2_scraper.py        # Y2 Intelligence
│   ├── elfa_scraper.py      # Elfa AI social
│   ├── x_scraper.py         # X / Twitter
│   ├── hyperliquid_scraper.py
│   ├── aster_scraper.py
│   └── polymarket_scraper.py
├── infrastructure/
│   └── nats/                # NATS server config
├── docs/                    # Architecture + setup docs
├── CAPABILITIES.md          # Full 57+ tool reference
├── docker-compose.yml
└── pyproject.toml
```

---

## License

Copyright © 2026 Morgan Fisher. All rights reserved. Viewing only — see [LICENSE](LICENSE).

---

<p align="center"><strong>Built by the <a href="https://github.com/hyper-sentinel">Hyper Sentinel</a> team · 6th Generation · March 2026</strong></p>
