# 🛡️ Hyper-Sentinel v2

**Autonomous Crypto Surveillance & Execution Agent — 5th Generation**

> 57+ tools · 20 @tool scrapers · 3 agent modes · 4 monitors · NATS pub/sub · Upsonic + Agno

5th Gen — rebuilt from the ground up on NATS, Upsonic Teams, and dual-framework agents. Same mission as [Sentinel v1](https://github.com/hyper-sentinel/agentic-hyper-sentinel): 24/7 autonomous operation with guardrails. New everything else.

---

## Generation Lineage

| Gen | Project | Key Upgrade |
|-----|---------|-------------|
| 1st | `fintech-terminal` | Single agent, foundation |
| 2nd | `agentic-fintech-terminal` | 5-agent swarm, 7 MCP servers |
| 3rd | `agentic-hyper-terminal` | Dual-DEX, FRED macro, browser automation |
| 4th | `agentic-hyper-sentinel` | Autonomous 24/7, monitors, missions, guardrails |
| **5th** | **`hyper-sentinel-v2`** | **NATS pub/sub, Upsonic Teams, @tool scrapers, coordinate mode** |

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
git clone https://github.com/hyper-sentinel/hyper-sentinel-v2.git && cd hyper-sentinel-v2 && docker compose up -d nats && uv run main.py
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
| **LLM Providers** | Claude · Gemini · Grok · Ollama (auto-fallback) |
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

### Team Agents (Upsonic)

| Agent | Role | Tools |
|-------|------|-------|
| 📊 **Analyst** | Research + TA | CRYPTO_TOOLS + MACRO_TOOLS + SENTIMENT_TOOLS |
| 🛡️ **RiskManager** | Risk assessment | ALL_TOOLS |
| ⚡ **Trader** | Execution | TRADING_TOOLS |

---

## 📊 57+ Tools Across 9 Domains

| Domain | Tools | Auth |
|--------|-------|------|
| **CoinGecko** | 3 | Free |
| **YFinance** | Stocks, options, fundamentals | Free |
| **FRED** | GDP, CPI, rates, yield curve, VIX | Free key |
| **Y2 / GloriaAI** | News sentiment, recaps, reports | API key |
| **Elfa AI** | Trending tokens, social mentions | API key |
| **X / Twitter** | Tweet search, sentiment | Bearer token |
| **Hyperliquid** | Perps trading, orderbook, positions | Wallet |
| **Aster DEX** | Futures, leverage, klines, funding | API key |
| **Polymarket** | Prediction markets, odds, trading | Free browse / key for trading |
| **TA Engine** | SMA, RSI, MACD, Bollinger | Built-in |
| **Guardrails** | Trade limits, kill switch, daily loss | Built-in |

---

## 🤖 Autonomous Architecture

```
┌─────────────────────────────────────────────────────┐
│                  SENTINEL RUNTIME                    │
│                                                     │
│  ┌──────────── MONITORS ──────────────┐            │
│  │ Price (15m) • Positions (30m)      │            │
│  │ Sentiment (60m) • Macro (6h)       │            │
│  └──────────────────────────────────────┘           │
│          ↓ threshold breach                         │
│  ┌──────────── TEAM ─────────────────┐             │
│  │ Analyst → RiskManager → Trader    │             │
│  │ 57+ tools • 20 @tool scrapers    │             │
│  └──────────────────────────────────────┘           │
│          ↓ decision                                 │
│  ┌──────────── GUARDRAILS ────────────┐            │
│  │ Max trade: $100 • Daily limit: 5   │            │
│  │ Max loss: $250 • Kill switch       │            │
│  └──────────────────────────────────────┘           │
│          ↓ execute / escalate                       │
│  ┌──────────── OUTPUT ────────────────┐            │
│  │ Telegram • NATS • Decision Log    │             │
│  └──────────────────────────────────────┘           │
│                                                     │
│  ┌──────────── MEMORY ────────────────┐            │
│  │ Decisions • Snapshots • Trades     │            │
│  │ SQLite (Upsonic Memory)            │            │
│  └──────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘
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
| `open <site>` | Open site in Chrome (youtube, tradingview, etc.) |
| `browse <url>` | Open any URL in your browser |
| `add` | Show available data source integrations |
| `add <service>` | Configure API key (hl, y2, elfa, fred, etc.) |
| `status` | Infrastructure dashboard |
| `logs [N]` | Last N decisions |
| `help` | All commands |
| `quit` | Shutdown |

---

## 📁 Project Structure

```
hyper-sentinel-v2/
├── main.py                  # Interactive REPL
├── sentinel.py              # Autonomous runtime loop
├── tools.py                 # 20 Upsonic @tool wrappers
├── monitors.py              # 4 continuous watchers
├── missions.py              # Standing orders system
├── memory.py                # Persistent state (SQLite → Postgres)
├── scheduler.py             # Cron-style task scheduler
├── strategy_runner.py       # SMA crossover auto-trading
├── ta_engine.py             # Technical analysis (pandas-ta)
├── telegram_client.py       # Telegram notifications
├── browser_agent.py         # 3-tier browser (fast open → LLM browse → computer use)
├── computer_use.py          # Safe computer control (apps, system info, shell)
├── agents/
│   ├── market-agent/        # Upsonic Agent + YFinanceTools
│   ├── analyst.py           # Research specialist
│   ├── trader.py            # Execution specialist
│   ├── risk_manager.py      # Risk specialist
│   └── swarm.py             # Agno 5-agent team
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
├── docker-compose.yml
└── pyproject.toml
```

---

## License

AGPL-3.0

---

**Built by the [Hyper Sentinel](https://github.com/hyper-sentinel) team**
