# Hyper-Sentinel: Technology Stack

## Core Philosophy

Every technology choice is made for one reason: **production-grade reliability at scale**. This is the same stack used by NASA for mission-critical telemetry, Cloudflare for global edge processing, and major financial institutions for high-frequency systems.

---

## Stack Overview

| Layer | Technology | Why |
|-------|-----------|-----|
| **Message Fabric** | NATS.io + JetStream | Nervous system. Pub/sub routing between all agents. Durable, persistent, fault-tolerant. |
| **Agent Workers** | Go (Golang) | Compiled, lightweight, embeds NATS natively. Ideal for performance-critical workers. |
| **Intelligence Layer** | Python + Upsonic | Agent framework, LLM orchestration, safety policies, multi-agent teams. |
| **Containerization** | Docker + Compose | One container per agent. Isolated, independently restartable, scalable. |
| **Persistent Memory** | SQLite → Postgres | Agent decisions, intel reports, audit trail. Queryable after the fact. |
| **Local LLM** | Ollama | Dev and testing. GPU-accelerated, private, no API costs. |
| **Cloud LLM — Reasoning** | Anthropic Claude | Primary reasoning, compliance, research agent intelligence. |
| **Cloud LLM — Data** | Gemini | High-throughput data processing. |
| **Cloud LLM — Speed** | Grok (xAI) | Latency-sensitive, real-time tasks. |
| **IDE / Code Gen** | Antigravity (Cursor fork) | AI-native development, agent skill generation. |
| **Governance** | Upsonic Safety Engine | Zero-trust policy enforcement on all agent inputs, outputs, tool calls. |
| **Operator Interface** | OpenClaw | Control the entire swarm from Telegram/Discord. |
| **Edge Ingestion** | synopsis (Go + NATS) | Raw data → structured messages → NATS fabric. |

---

## NATS.io — The Nervous System

NATS is the backbone of Hyper-Sentinel. It is not a simple message queue — it is a high-performance distributed messaging system built for mission-critical workloads.

**Why NATS over alternatives (Kafka, RabbitMQ, Redis Pub/Sub):**

- Embedded in Go binaries — no separate broker required per agent
- JetStream adds durable, persistent, exactly-once delivery
- Sub-millisecond latency — critical for market data processing
- Used by NASA, Cloudflare, VMware in production
- Wildcard subject routing: `sentinel.market.*`, `sentinel.risk.*`, `sentinel.compliance.*`

**Subject Architecture:**

```
sentinel.market.data        ← Raw market feed ingestion
sentinel.market.signal      ← Market Agent output
sentinel.risk.input         ← Risk Agent trigger
sentinel.risk.alert         ← Risk Agent output
sentinel.compliance.check   ← Compliance Agent trigger
sentinel.compliance.clear   ← Compliance Agent approval
sentinel.research.request   ← Research Agent trigger
sentinel.research.report    ← Research Agent output
sentinel.execution.stage    ← Execution Agent staging
sentinel.governance.approve ← Sentinel approval required
sentinel.governance.audit   ← Audit log stream
```

---

## Go (Golang) — The Worker Layer

Go is the language of distributed systems infrastructure. Lightweight binaries, embedded NATS, Docker-friendly, compiled to a single executable.

**Used for:**
- Agent worker containers (gogent pattern)
- Edge data ingestion (synopsis pattern)
- NATS message routing and transformation
- High-frequency data processing

---

## Python + Upsonic — The Intelligence Layer

Python handles LLM orchestration, agent logic, and swarm coordination. Upsonic is the production-ready fintech agent framework built on top.

**Upsonic key components:**
- `Agent` — base agent class, multi-provider LLM support
- `AutonomousAgent` — sandboxed filesystem + shell access
- `Safety Engine` — policy enforcement at input/output/tool level
- `Memory` — session memory with persistent storage backends
- `Teams` — multi-agent sequential and parallel coordination

---

## Ollama — Local Dev Inference

Ollama runs LLM models locally on GPU. Used during development to:
- Test agent logic without burning API credits
- Develop offline or in secure environments
- Run the Ryzen 7600X + 12GB GPU as a local inference server

**Recommended models for Hyper-Sentinel dev:**
- `deepseek-r1:7b` — reasoning tasks
- `llama3.2:3b` — fast, lightweight for quick tests
- `mistral:7b` — balanced speed/quality

---

## Docker — The Isolation Layer

One container per agent. Each agent has:
- Its own Dockerfile
- Its own environment variables (API keys injected, never hardcoded)
- Its own volume for persistent data
- Health checks with auto-restart on failure

```
hyper-sentinel/
├── docker-compose.yml          ← Orchestrates all agents
├── agents/
│   ├── market-agent/
│   │   └── Dockerfile
│   ├── risk-agent/
│   │   └── Dockerfile
│   ├── compliance-agent/
│   │   └── Dockerfile
│   ├── research-agent/
│   │   └── Dockerfile
│   └── execution-agent/
│       └── Dockerfile
└── infrastructure/
    ├── nats/
    │   └── nats-server.conf
    └── sqlite/
```

---

## Dev Machine vs Deploy Machine

| | MacBook Pro | PC (Ryzen 7600X) |
|-|-------------|-----------------|
| **Role** | Development, testing, iteration | 24/7 deployment target |
| **LLM** | Ollama (Apple Silicon) | Ollama (12GB GPU) |
| **Docker** | Docker Desktop for Mac | Docker Desktop for Windows |
| **NATS** | Local single node | Cluster mode (Phase 5) |
