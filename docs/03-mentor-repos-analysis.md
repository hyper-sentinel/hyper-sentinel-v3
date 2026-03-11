# Mentor Codebase Analysis: github.com/tobalo

## Architectural Thread

Every project tobalo has built shares one philosophy: **lightweight, composable, distributed AI workers connected by a message fabric — not monolithic AI applications.**

The recurring pattern:
```
Raw Data / Events → NATS pub/sub → Agentic Worker Swarm → LLM → Structured Output → Persistent Storage
```

---

## tobalo/gogent ⭐ CRITICAL

**[github.com/tobalo/gogent](https://github.com/tobalo/gogent)**

> Agentic AI workers explicitly in Go

**What it is:** A distributed real-time log analysis system demonstrating the complete pattern for containerized agentic workers. Embeds NATS directly inside the Go binary — the message bus and agent are a single deployable unit. LLM agents subscribe to a NATS subject, process messages, analyze with LLM, persist to SQLite.

**Key decisions:**
- **Embedded NATS** — no separate broker. The agent IS the bus.
- **JetStream persistence** — messages durable, replayed on restart, never lost
- **Multi-provider LLM** — one config switch: Ollama, Claude, Gemini, OpenAI, DeepSeek, Azure
- **SQLite storage** — agent decisions queryable via SQL after the fact
- **Docker Compose ready** — `docker-compose up -d` gives a running agent in 30 seconds

**Architecture:**
```
IoT Log Producers
    │
    ▼ (NATS publish)
agent.technical.support subject
    │
    ▼ (NATS subscribe)
Agent Sig (Go LLM worker)
    │
    ▼
SQLite DB (analysis + original log stored)
```

**Config schema:**
```go
type Config struct {
    APIKey       string  // Claude / Gemini / OpenAI key
    NATSUrl      string  // nats://localhost:4222
    AgentName    string
    Instructions string
    Model        string
    Provider     string  // OLLAMA | CLAUDE | GEMINI | OPENAI
    DBPath       string
}
```

**Hyper-Sentinel mapping:**

| gogent concept | Hyper-Sentinel equivalent |
|---------------|--------------------------|
| `agent.technical.support` | `sentinel.market.data`, `sentinel.risk.alert` |
| Embedded NATS | Per-agent NATS or shared cluster |
| Multi-provider config | Claude reasoning, Gemini data, Grok speed |
| SQLite analysis | Full audit trail per agent decision |
| docker-compose.yml | Hyper-Sentinel multi-container deployment template |

---

## tobalo/agentic-osint ⭐ CRITICAL

**[github.com/tobalo/agentic-osint](https://github.com/tobalo/agentic-osint)**

> Prototype of generating intel reports on pub/sub triggers with AI agents

**What it is:** A working prototype pub/sub triggered agentic swarm for intelligence report generation. The README explicitly names **financial market analysis and OSINT** as primary use cases. This is the direct ancestor of Hyper-Sentinel's Research Agent.

**How it works:**
1. NATS server runs locally
2. Messages published to `swarm.*` subjects
3. `swarm.py` subscribes, receives trigger, spins up agent swarm
4. Agents research topic, cross-reference sources, compile findings
5. Output: structured intelligence report saved to `example_reports/`

**Example triggers:**
```bash
nats pub swarm.markets "analyze unusual SPY volume today"
nats pub swarm.risk "flag macro events that could impact tech sector"
nats pub swarm.compliance "check recent SEC filings for NVDA insider activity"
```

**File structure:**
```
agentic-osint/
├── swarm.py           ← Core orchestrator — NATS subscriber + agent spawner
├── pkg/shared.py      ← Shared config: NATS URL, queue names
├── example_reports/   ← Study these — this is your output baseline
├── requirements.txt   ← OpenAI Swarm, NATS client
└── test.sh            ← Publish test messages, validate swarm
```

**Hyper-Sentinel role:** This IS Phase 1 of Hyper-Sentinel's Research Agent. Fork `swarm.py`, swap OpenAI for Claude via Upsonic, point NATS subjects at your fintech-terminal feeds. Working financial intelligence swarm in hours, not weeks.

---

## tobalo/synopsis ⭐ HIGH

**[github.com/tobalo/synopsis](https://github.com/tobalo/synopsis)**

> EdgeAI CLI — raw edge data & SIGINT to natural language intelligence via NATS

**What it is:** Go CLI tool that sits at the **data ingestion layer** — takes raw, unstructured edge data and converts it to structured intelligence via NATS + LLM. Built during an Accenture Oracle Hackathon for a multi-domain data fabric use case.

**Why it matters:**
- The bridge between raw data sources and the agent intelligence layer
- Dockerized with clean Dockerfile
- Uses NATS as transmission fabric — same as gogent, same as agentic-osint
- The fintech-terminal data flows through this layer into NATS

**Data flow:**
```
Market Feed / Raw Data
    ↓
synopsis (Go — edge ingestion)
    ↓
edge.ai.synopsis (NATS subject)
    ↓
Agent Swarm (agentic-osint pattern)
    ↓
Intelligence Reports
    ↓
Hyper-Sentinel Governance
```

---

## tobalo/ai-agent-hello-world ⭐ MEDIUM

**[github.com/tobalo/ai-agent-hello-world](https://github.com/tobalo/ai-agent-hello-world)**

> Private AI agents with Agno and Ollama — beginner friendly

**What it is:** Foundation repo. Uses Agno (formerly Phidata) + Ollama + uv. Your local dev baseline before adding NATS and multi-agent coordination.

**Why it matters:**
- Uses `uv` — your existing package manager
- Agno pairs well with Upsonic for agent definitions
- Ollama for local dev — test without burning API credits
- The architecture diagram is the clearest visual of agent internals

**Local dev strategy:** Build with Ollama, deploy with Claude/Gemini/Grok. Same code, different provider config.

---

## tobalo/oracle23ai-llm-examples ⭐ FUTURE

**[github.com/tobalo/oracle23ai-llm-examples](https://github.com/tobalo/oracle23ai-llm-examples)**

> Lab samples of using OLLAMA with Oracle DB 23ai

**What it is:** LLM integration with Oracle Database 23ai — AI-native database with built-in vector search, semantic similarity, and RAG.

**Future relevance (Phase 5+):**
- Oracle 23ai vector search → semantic agent memory retrieval
- RAG on financial documents: 10-Ks, earnings calls, SEC filings
- Enterprise-grade persistent memory for production Hyper-Sentinel
- SQLite → Postgres → Oracle 23ai is the memory progression

---

## The Complete tobalo Pattern

```
synopsis (Go)           → Edge data ingestion → NATS
gogent (Go)             → Agent worker template → Docker Compose
agentic-osint (Python)  → Swarm orchestration → Intel reports
ai-agent-hello-world    → Local dev baseline → Agno + Ollama + uv
oracle23ai              → Future enterprise memory → RAG + vector search
```

Every repo is a module. Hyper-Sentinel is the assembly.
