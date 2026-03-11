# 🏗️ Hyper-Sentinel v3 — Architecture & Trading Setup

> System design, event-driven architecture, and step-by-step setup for all three trading venues.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Agent Chain & NATS Subjects](#agent-chain--nats-subjects)
3. [Design Rules](#design-rules)
4. [Technology Stack](#technology-stack)
5. [Decision Database Schema](#decision-database-schema)
6. [Hyperliquid Setup](#-hyperliquid-setup)
7. [Aster DEX Setup](#-aster-dex-setup)
8. [Polymarket Setup](#-polymarket-setup)

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    HYPER-SENTINEL v3 RUNTIME                      │
│                                                                  │
│   ┌─── LLM LAYER ─────────────────────────────────────────────┐ │
│   │  Claude · Gemini · Grok · Ollama                          │ │
│   │  Auto-detect from key prefix · Switch mid-session         │ │
│   └───────────────────────────────────────────────────────────┘ │
│                           ↕ tool calls                           │
│   ┌─── AGENT LAYER ───────────────────────────────────────────┐ │
│   │  Solo (1 agent) · Swarm (5 Agno) · Team (3 Upsonic)      │ │
│   │  57+ tools · Shared memory · Safety policies              │ │
│   │                                                           │ │
│   │  Swarm: Captain → Analyst, Trader, Risk, Ops              │ │
│   │  Team:  Analyst → RiskManager → Trader (coordinate)       │ │
│   └───────────────────────────────────────────────────────────┘ │
│                           ↕ NATS pub/sub                         │
│   ┌─── DATA LAYER ────────────────────────────────────────────┐ │
│   │  CoinGecko · YFinance · FRED · Y2 · Elfa · X             │ │
│   │  Hyperliquid SDK · Aster REST · Polymarket CLOB           │ │
│   └───────────────────────────────────────────────────────────┘ │
│                           ↕ events                               │
│   ┌─── AUTONOMOUS LAYER ─────────────────────────────────────┐ │
│   │  Monitors: Price (15m) · Position (30m) · Sentiment (60m)│ │
│   │            Macro (6h) — threshold-based, zero LLM cost   │ │
│   │  Missions: Trail Stop · Briefing · Alert · DCA · Rebal   │ │
│   │  Guardrails: $100/trade · 5/day · $250 loss · Kill SW    │ │
│   └───────────────────────────────────────────────────────────┘ │
│                           ↕ execution                            │
│   ┌─── BROWSER + COMPUTER CONTROL ───────────────────────────┐ │
│   │  Tier 1: Chrome direct (webbrowser)                       │ │
│   │  Tier 2: LLM + Playwright (browser-use)                  │ │
│   │  Tier 3: Anthropic Computer Use (full desktop control)    │ │
│   │  Docker-isolated shell execution                          │ │
│   └───────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Agent Chain & NATS Subjects

### Event Flow

```
sentinel.market.data       → MarketAgent      → sentinel.risk.input
sentinel.risk.input        → RiskAgent        → sentinel.compliance.check
sentinel.compliance.check  → ComplianceAgent  → sentinel.governance.approve
sentinel.governance.approve → ExecutionAgent  (sandboxed, approval-gated)
sentinel.research.request  → ResearchAgent    → sentinel.research.report
sentinel.governance.audit  → ALL decisions logged (JetStream durable)
```

### NATS Subject Map

| Subject | Publisher | Subscriber | Purpose |
|---------|-----------|------------|---------|
| `sentinel.market.data` | Monitors / Scheduler | MarketAgent | Trigger market analysis |
| `sentinel.risk.input` | MarketAgent | RiskAgent | Analysis results for risk assessment |
| `sentinel.compliance.check` | RiskAgent | ComplianceAgent | Risk-assessed data for compliance |
| `sentinel.governance.approve` | ComplianceAgent | ExecutionAgent | Approved actions for execution |
| `sentinel.research.request` | Any agent | ResearchAgent | Ad-hoc research requests |
| `sentinel.alerts.*` | Any | Telegram + Logs | Alert notifications |
| `sentinel.missions.*` | Scheduler | Sentinel | Mission triggers |
| `sentinel.governance.audit` | ALL agents | Audit trail | Every decision logged (JetStream durable) |

---

## Design Rules

1. **Zero-trust** — nothing executes without governance approval
2. **Fail-secure** — if Sentinel layer errors, all actions **block**, never pass through
3. **One agent = one container** — full isolation (Docker Compose)
4. **All communication via NATS** — no direct function calls between agents
5. **Everything logged** — every agent decision → SQLite with full context
6. **Model-agnostic** — provider is an environment variable, auto-detected from key prefix

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Messaging** | NATS.io + JetStream | Pub/sub fabric, durable persistence |
| **Intelligence** | Python + Upsonic + Agno | LLM orchestration, safety, multi-agent teams |
| **Containers** | Docker + Compose | One container per agent, isolated networks |
| **Database** | SQLite (dev) → Postgres (prod) | Decision audit trail |
| **Primary LLM** | Anthropic Claude | Reasoning, analysis, compliance |
| **Secondary LLMs** | Gemini (throughput), Grok (speed), Ollama (local) | Specialized workloads |
| **Browser** | Playwright + browser-use | Tier 2 LLM-driven automation |
| **Trading SDKs** | hyperliquid-python-sdk, requests (Aster), py-clob-client (Polymarket) | Multi-venue execution |
| **Terminal UI** | Rich | Tables, panels, progress bars |
| **Deploy** | Docker Compose → Cloud Run | Local → production |

---

## Decision Database Schema

Every agent decision is logged with full context:

```sql
CREATE TABLE agent_decisions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    NOT NULL,
    agent_name      TEXT    NOT NULL,
    subject         TEXT    NOT NULL,
    input_data      TEXT    NOT NULL,
    output_data     TEXT,
    decision        TEXT,
    confidence      REAL,
    provider        TEXT    NOT NULL,
    model           TEXT    NOT NULL,
    latency_ms      INTEGER,
    status          TEXT    DEFAULT 'completed',
    error           TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## ⚡ Hyperliquid Setup

> SDK: [hyperliquid-python-sdk](https://github.com/hyperliquid-dex/hyperliquid-python-sdk) · DEX: [hyperliquid.xyz](https://hyperliquid.xyz)

### What Is Hyperliquid?

Hyperliquid is a **decentralized perpetual futures exchange** on its own L1 blockchain. USDC-margined, up to 50x leverage, 200+ trading pairs, on-chain order book with sub-second finality. No gas fees.

### Two Access Levels

| Mode | `.env` Variables | Agent Can Do |
|------|-----------------|-------------|
| **Read-only** | `HYPERLIQUID_WALLET=0x...` | View account, positions, orderbook |
| **Trading** | `HYPERLIQUID_WALLET=0x...` + `HYPERLIQUID_PRIVATE_KEY=0x...` | Everything + place/cancel orders |

### API Wallet vs. Main Wallet

> ⚠️ **Never use your MetaMask private key.** Always create an API wallet.

| Feature | Main Wallet (MetaMask) | API Wallet |
|---------|----------------------|------------|
| **Can trade?** | Yes | ✅ Yes — designed for bots |
| **Can withdraw?** | Yes | ❌ **NO** |
| **Revocable?** | No | ✅ Yes — revoke anytime |
| **Risk if leaked** | **Full wallet drain** | **Trading only** — funds safe |

### Step-by-Step: Getting API Keys

1. Go to [app.hyperliquid.xyz](https://app.hyperliquid.xyz) → connect MetaMask
2. Click **More** → **API** → **Generate API Wallet**
3. Name it `hyper-sentinel-v3`
4. ⚠️ **Copy the private key immediately** — shown only once
5. Click **Authorize API Wallet** → confirm MetaMask transaction

### `.env` Configuration

```bash
# Main wallet address (for read operations)
HYPERLIQUID_WALLET=0xYourMainWalletAddress

# API wallet private key (for trading — NOT your MetaMask key!)
HYPERLIQUID_PRIVATE_KEY=0xYourApiWalletPrivateKeyHere
```

### In-Terminal Setup

```
⚡ You → add hl
  Paste wallet address: 0x...
  Paste API private key: 0x...
  ✅ Saved to .env
```

### Funding Your Account

1. Buy USDC on any exchange
2. Send USDC to MetaMask on **Arbitrum** network
3. Connect MetaMask to [app.hyperliquid.xyz](https://app.hyperliquid.xyz)
4. Deposit USDC (minimum ~$10)

### VPN Workaround

If you need a VPN for the browser but it breaks Python API calls:
- **Split tunnel**: Bypass Terminal/Python from VPN routing
- **Two-phase**: VPN ON → generate API key in browser → VPN OFF → run terminal
- The API endpoint (`api.hyperliquid.xyz`) typically does NOT require VPN

### Supported Pairs

| Tier | Coins | Max Leverage |
|------|-------|-------------|
| **Major** | BTC, ETH | 50x |
| **Large Cap** | SOL, DOGE, AVAX, LINK | 20-50x |
| **Mid Cap** | ARB, OP, SUI, SEI, INJ | 10-20x |
| **Meme** | WIF, PEPE, BONK, FLOKI | 5-10x |

Full list: [app.hyperliquid.xyz/trade](https://app.hyperliquid.xyz/trade)

### Security Best Practices

- ✅ Use an **API wallet** (not MetaMask key)
- ✅ Store keys in `.env` (gitignored)
- ✅ Set expiration on API wallet and regenerate periodically
- ✅ Test on **testnet** first (`api.hyperliquid-testnet.xyz`)
- ❌ Never commit `.env` to version control

---

## 🌟 Aster DEX Setup

> DEX: [asterdex.com](https://www.asterdex.com) · Auth: HMAC-SHA256 (V1 API)

### What Is Aster?

Aster is a **decentralized futures exchange** with up to 125x leverage, similar to Binance Futures but on-chain. Hyper-Sentinel uses the **V1 API** with HMAC authentication.

### Two API Versions

| Feature | V1 (Standard) ← **We Use This** | V3 (Pro / Agent Wallet) |
|---------|----------------------------------|------------------------|
| **Auth** | HMAC-SHA256 | Web3 EIP-712 Signature |
| **Credentials** | API Key + Secret | Wallet + Signer + Private Key |
| **Setup** | API Management page | api-wallet page |
| **Best for** | Bots, scripts | Delegated agents |

### Step-by-Step: Getting API Keys

1. Go to [asterdex.com](https://www.asterdex.com) → connect wallet
2. Navigate to **API Management**
3. Click **Create API Key**
4. ⚠️ **Enable "Futures Trading" permission** — without this, trades fail with `-2015`
5. Optionally whitelist your IP
6. Save both API Key and Secret — **Secret shown only once**

### `.env` Configuration

```bash
# V1 API — Standard HMAC
ASTER_API_KEY=your_64_char_hex_api_key
ASTER_API_SECRET=your_64_char_hex_api_secret
```

### In-Terminal Setup

```
⚡ You → add aster
  Paste API Key: ...
  Paste API Secret: ...
  ✅ Saved to .env
```

### Common Error Codes

| Code | Name | Fix |
|------|------|-----|
| -1022 | INVALID_SIGNATURE | Check secret key matches API key |
| -2015 | REJECTED_MBX_KEY | **Enable Futures Trading permission** |
| -2018 | BALANCE_NOT_SUFFICIENT | Deposit more funds |
| -2027 | MAX_LEVERAGE_RATIO | Reduce leverage |

### Diagnostics

```
⚡ You → run aster diagnostics
  connectivity: ✅ OK
  time_sync: ✅ OK (72ms drift)
  get_auth: ✅ Read access working
  post_auth: ✅ Trading access working
```

---

## 🔮 Polymarket Setup

> DEX: [polymarket.com](https://polymarket.com) · SDK: [py-clob-client](https://github.com/Polymarket/py-clob-client)

### What Is Polymarket?

Polymarket is the world's largest **prediction market** — bet on real-world events (elections, sports, crypto, geopolitics). Markets show probability-based odds that update in real-time based on trading activity.

### Two Access Levels

| Mode | What You Need | Agent Can Do |
|------|--------------|-------------|
| **Browse** | Nothing | View markets, odds, volume |
| **Trading** | API Key + Secret + Passphrase | Place/cancel orders, view positions |

### Getting API Credentials

1. Go to [polymarket.com](https://polymarket.com) → connect wallet
2. Navigate to **Settings** → **API Keys**
3. Generate a new API key
4. Save: API Key, API Secret, API Passphrase

### `.env` Configuration

```bash
# Polymarket CLOB API
POLYMARKET_API_KEY=your_api_key
POLYMARKET_API_SECRET=your_api_secret
POLYMARKET_PASSPHRASE=your_passphrase
POLYMARKET_FUNDER=0xYourWalletAddress
```

### In-Terminal Setup

```
⚡ You → add poly
  Paste API Key: ...
  Paste API Secret: ...
  Paste Passphrase: ...
  ✅ Saved to .env
```

### How Prediction Markets Work

```
Market: "Will BTC hit $100K by June 2026?"
  YES: $0.72 (72% probability) — buy if you think it will
  NO:  $0.28 (28% probability) — buy if you think it won't
  
If you're right → payout = $1.00 per share
If you're wrong → payout = $0.00
```

### Example Session

```
⚡ You → Show me trending prediction markets
Agent → Top markets by volume:
  1. "Will BTC hit $100K by June?" — YES: 72¢ | Vol: $2.3M
  2. "Fed rate cut in July?" — YES: 41¢ | Vol: $1.8M
  3. "ETH above $5000 by Q3?" — YES: 38¢ | Vol: $950K

⚡ You → Buy 100 YES shares on "BTC 100K"
Agent → ⚠️ Confirm: BUY 100 YES @ $0.72 ($72.00 total)?
⚡ You → Yes
Agent → ✅ Order filled: 100 YES shares @ $0.72
```

---

## 📁 Project Structure

```
hyper-sentinel-v3/
├── main.py                  # Interactive REPL + command routing
├── sentinel.py              # Autonomous runtime loop
├── browser_agent.py         # 3-tier browser automation
├── computer_use.py          # Safe computer control
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
├── agents/
│   └── market-agent/        # Upsonic Agent + YFinanceTools
├── scrapers/
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
├── docs/
├── CAPABILITIES.md          # 57+ tool reference
├── ARCHITECTURE.md          # ← You are here
├── docker-compose.yml
└── pyproject.toml
```

---

## Environment Variables — Complete Reference

| Variable | Required? | Purpose |
|----------|-----------|---------|
| `ANTHROPIC_API_KEY` | One LLM key required | Claude provider |
| `GEMINI_API_KEY` | One LLM key required | Gemini provider |
| `XAI_API_KEY` | One LLM key required | Grok provider |
| `HYPERLIQUID_WALLET` | For HL features | Main wallet address |
| `HYPERLIQUID_PRIVATE_KEY` | For HL trading | API wallet private key |
| `ASTER_API_KEY` | For Aster features | V1 API key |
| `ASTER_API_SECRET` | For Aster trading | V1 API secret |
| `POLYMARKET_API_KEY` | For Poly trading | CLOB API key |
| `POLYMARKET_API_SECRET` | For Poly trading | CLOB API secret |
| `POLYMARKET_PASSPHRASE` | For Poly trading | CLOB passphrase |
| `POLYMARKET_FUNDER` | For Poly trading | Wallet address |
| `Y2_API_KEY` | For news intel | Y2 Intelligence |
| `ELFA_API_KEY` | For social sentiment | Elfa AI |
| `X_BEARER_TOKEN` | For X data | Twitter/X API |
| `FRED_API_KEY` | For macro data | FRED (free key) |
| `TELEGRAM_BOT_TOKEN` | For notifications | Telegram bot |
| `TELEGRAM_CHAT_ID` | For notifications | Chat to send to |
| `SENTINEL_MAX_TRADE_USD` | Optional | Max trade size (default: $100) |
| `SENTINEL_MAX_DAILY_TRADES` | Optional | Max trades/day (default: 5) |
| `SENTINEL_MAX_DAILY_LOSS` | Optional | Max daily loss (default: $250) |

---

**Built by the [Hyper Sentinel](https://github.com/hyper-sentinel) team · 6th Generation · March 2026**
