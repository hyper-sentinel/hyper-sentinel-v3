# 🔍 Agentic Features Audit — v1 vs v3

**Date:** March 12, 2026  
**Scope:** agentic-hyper-sentinel (v1) → hyper-sentinel-v3

---

## Feature Comparison Matrix

| # | Feature | v1 (agentic-hyper-sentinel) | v3 (hyper-sentinel-v3) | Integration Priority |
|---|---------|---------------------------|----------------------|---------------------|
| 1 | **Telegram Client (Telethon)** | ✅ Full: `tg chats`, `tg read`, `tg send`, PepeBoost | ⚠️ File exists, commands not wired | 🔴 HIGH |
| 2 | **Telegram Bot** | ✅ `telegram_bot.py`, auto-start in sentinel | ⚠️ `add telegram` saves token, no bot handler | 🟡 MEDIUM |
| 3 | **`add tg client` setup** | ✅ API_ID + API_HASH + Phone + verify | ❌ Missing from `_ADD_SERVICES` | 🔴 HIGH |
| 4 | **Discord Bot** | ✅ `add discord`, token + channel | ❌ Not in v3 | 🟢 LOW |
| 5 | **GitHub MCP** | ✅ `add github`, repos + issues | ❌ Not in v3 | 🟢 LOW |
| 6 | **Postgres MCP** | ✅ `add postgres`, SQL queries | ❌ Not in v3 | 🟢 LOW |
| 7 | **Brave Search MCP** | ✅ `add brave`, web search for swarm | ❌ Not in v3 | 🟢 LOW |
| 8 | **Scheduler** | ✅ `add scheduler`, cron-style jobs | ⚠️ Exists in sentinel.py, not in REPL | 🟡 MEDIUM |
| 9 | **IPC / Shared State** | ✅ `add ipc`, agent-to-agent coordination | ❌ Not in v3 | 🟢 LOW |
| 10 | **Memory System** | ✅ `memory`, `clear memory`, persistent | ❌ Not in v3 REPL | 🟡 MEDIUM |
| 11 | **Browser / Computer Use** | ✅ 3-tier: open, browse, computer_use | ✅ `browser_agent.py`, `open` commands | ✅ Done |
| 12 | **SMA Strategy** | ✅ `add strategy`, SMA crossover algo | ❌ Not in v3 | 🟢 LOW |
| 13 | **Swarm Mode (5 agents)** | ✅ Captain + Analyst + Trader + Risk + Ops | ✅ Swarm mode available | ✅ Done |
| 14 | **Team Mode (Upsonic)** | ❌ N/A | ✅ New in v3 | ✅ Done |
| 15 | **Sentinel Autonomous Loop** | ✅ 4 monitors + missions | ✅ Same pattern, improved | ✅ Done |
| 16 | **REST API (SaaS)** | ❌ N/A | ✅ 49 tools, auto-start | ✅ Done |
| 17 | **NATS / JetStream** | ❌ N/A | ✅ New in v3 | ✅ Done |
| 18 | **Docker / Compose** | ❌ N/A | ✅ NATS containerized | ✅ Done |
| 19 | **TradingView Webhooks** | ✅ webhook_server.py | ✅ Carried forward | ✅ Done |

---

## Telegram Client — What v1 Had (and v3 Needs)

### v1 Commands (fully wired in main.py)

```
add tg client     → API_ID + API_HASH + Phone → Telethon connect → verify
tg chats          → List all chats/channels/groups/bots
tg read @channel  → Read last 10 messages from any chat
tg send @bot msg  → Send message to any user/bot/group
```

### v1 PepeBoost Integration

The v1 `telegram_client.py` docstring explicitly says:
> "Send messages to any chat, group, or bot (e.g. **PepeBoost**)"

The setup flow says:
> "Connects as YOU — read channels, send to bots (PepeBoost, etc.)"

This means you could:
1. Sign in as your Telegram account
2. `tg chats` to see all your chats including PepeBoost
3. `tg read @pepeboost_bot` to read signals
4. `tg send @pepeboost_bot /buy ETH 0.1` to execute trades via the bot

### v3 Current State

- `telegram_client.py` **exists and is identical** (272 lines, same `TelegramUserClient` class)
- But the `tg chats`, `tg read`, `tg send` commands are **NOT wired** in v3's `main.py`
- `add tg client` setup flow (API_ID + API_HASH + Phone) is **NOT in v3**
- `add telegram` only saves `TELEGRAM_BOT_TOKEN` (for notifications), not the client API

### What Needs to Happen

1. Add `add tg client` to `_ADD_SERVICES` (API_ID, API_HASH, TELEGRAM_PHONE)
2. Wire `tg chats`, `tg read`, `tg send` commands in v3's REPL loop
3. PepeBoost integration works automatically once Telegram Client is connected

---

## Features v3 Gained That v1 Didn't Have

| Feature | Notes |
|---------|-------|
| **NATS / JetStream** | Pub-sub messaging, 7-day retention |
| **Docker Compose** | Containerized infrastructure |
| **REST API (SaaS)** | 49 tools as HTTP endpoints, auth tiers |
| **Team Mode (Upsonic)** | 3-agent coordinated team |
| **`add api` command** | SaaS key management |
| **Auto-verify on add** | Every `add` command verifies the key works |

---

## Recommended Integration Roadmap

### Phase 1 — Telegram Client (PepeBoost) 🔴
Port `tg chats`, `tg read`, `tg send` commands and `add tg client` setup from v1 → v3.
**LOE:** ~2 hours — the `telegram_client.py` is identical, just need to wire commands.

### Phase 2 — Memory System 🟡
Port `memory`, `clear memory` commands. Agent learns facts from conversations.
**LOE:** ~1 hour — `mem0` integration from v1.

### Phase 3 — Telegram Bot Handler 🟡
Wire `telegram_bot.py` to run as daemon thread (like REST API). Enables getting alerts on your phone and replying to Sentinel from Telegram.
**LOE:** ~1 hour.

### Phase 4 — Optional (Low Priority) 🟢
- Discord bot, GitHub MCP, Postgres MCP, Brave MCP, Scheduler, IPC, SMA Strategy
- These are nice-to-haves. Only needed for specific use cases.

---

*Audit generated from source code analysis of agentic-hyper-sentinel and hyper-sentinel-v3*
