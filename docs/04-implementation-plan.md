# Hyper-Sentinel v2: Implementation Plan

## Vision

Build a **NASA/Cloudflare-tier autonomous fintech AI agent system** using NATS.io, Golang, Docker, SQLite, Ollama, and multi-agent swarms — grounded in the proven patterns from `github.com/tobalo` and `github.com/Upsonic/Upsonic`.

---

## Phase 1 — Clone, Run, Understand
**Timeline: Week 1 | Goal: Get all mentor repos running locally**

### Tasks

- [ ] Clone all three core repos
  ```bash
  git clone https://github.com/tobalo/gogent.git
  git clone https://github.com/tobalo/agentic-osint.git
  git clone https://github.com/tobalo/ai-agent-hello-world.git
  ```
- [ ] Install NATS server
  ```bash
  brew install nats-server   # Mac
  # or: choco install nats-server  # Windows
  ```
- [ ] Run gogent
  ```bash
  cd gogent && docker-compose up -d
  nats pub agent.technical.support '{"severity":"ERROR","message":"test"}'
  ```
- [ ] Run agentic-osint
  ```bash
  cd agentic-osint
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  python3 swarm.py &
  nats pub swarm.markets "analyze SPY volume anomalies today"
  ```
- [ ] Study `example_reports/` output — this is your baseline
- [ ] Run ai-agent-hello-world with Ollama local model
- [ ] Install Upsonic: `uv pip install upsonic`

### Milestone
> Live, running agent swarm on Mac responding to NATS triggers and generating intelligence reports.

---

## Phase 2 — Build Hyper-Sentinel Core Agents
**Timeline: Weeks 2–3 | Goal: Specialized fintech agents via Upsonic + Claude**

### Agent Definitions

#### MarketAgent
```python
from upsonic import Agent, Task
from upsonic.tools.common_tools import YFinanceTools

market_agent = Agent(
    model="anthropic/claude-sonnet-4-5",
    name="HyperSentinel_Market"
)
task = Task(
    description="Monitor SPY, QQQ, BTC — flag unusual volume or momentum divergence",
    tools=[YFinanceTools()]
)
```
- **Subscribes to:** `sentinel.market.data`
- **Publishes to:** `sentinel.risk.input`

#### RiskAgent
- **Subscribes to:** `sentinel.risk.input`
- **Tools:** Custom risk threshold evaluator
- **Policy:** Blocks outputs above defined exposure limit
- **Publishes to:** `sentinel.compliance.check`

#### ComplianceAgent
- **Subscribes to:** `sentinel.compliance.check`
- **Policies:** `PIIAnonymizePolicy`, `FinancialDataPolicy`
- **Publishes to:** `sentinel.research.request` or `sentinel.governance.approve`

#### ResearchAgent
- **Type:** `AutonomousAgent` (sandboxed workspace)
- **Subscribes to:** `sentinel.research.request`
- **Capability:** Deep dives on tickers, sectors, macro events, SEC filings
- **Publishes to:** `sentinel.research.report`

#### ExecutionAgent
- **Type:** `AutonomousAgent` (sandboxed, restricted)
- **Subscribes to:** `sentinel.governance.approve`
- **Rule:** Nothing executes without explicit Sentinel Governor approval

### Tasks
- [ ] Implement MarketAgent → test with live SPY/QQQ data
- [ ] Implement RiskAgent → validate threshold policies
- [ ] Implement ComplianceAgent → PIIAnonymizePolicy + FinancialDataPolicy
- [ ] Implement ResearchAgent → test SEC filing research
- [ ] Wire all agents via NATS subjects
- [ ] One Dockerfile per agent
- [ ] docker-compose.yml orchestrating all 4 agents + NATS

### Milestone
> 4-agent swarm (Market → Risk → Compliance → Research) communicating via NATS, each in Docker, all powered by Claude.

---

## Phase 3 — Sentinel Governance Layer
**Timeline: Week 4 | Goal: Zero-trust approval on every agent action**

### Tasks
- [ ] Upsonic Safety Engine policies on ALL agents
- [ ] Integrate `azdhril/Sentinel` `@protect` decorator on ExecutionAgent
  ```python
  from sentinel import protect, SentinelConfig
  config = SentinelConfig(rules_path="rules.json")

  @protect(config)
  async def execute_trade(amount: float, ticker: str) -> str:
      return f"Staged: {amount} of {ticker}"
  ```
- [ ] Approval interface: terminal prompt + optional Telegram via OpenClaw
- [ ] Full audit trail: every agent decision → SQLite
  - timestamp, model used, NATS subject, input hash, output, policy decision
- [ ] Z-score anomaly detection on agent outputs
- [ ] Dead man's switch: Sentinel layer down → all execution blocked

### Milestone
> No agent action executes without governance. Full audit log queryable via SQL. System fails secure.

---

## Phase 4 — Antigravity Integration & Self-Improvement
**Timeline: Weeks 5–6 | Goal: Agents that write their own playbooks**

### Tasks
- [ ] Feed entire Hyper-Sentinel codebase into Antigravity as context
- [ ] Configure Antigravity to read Upsonic skill patterns
- [ ] MarketAgent detects new pattern → proposes new Task definition
- [ ] Proposed skills → Sentinel governance → operator approval → deployment
- [ ] Connect OpenClaw as operator interface
  ```bash
  # From Telegram/Discord:
  "Analyze NVDA earnings"          → triggers ResearchAgent via NATS
  "Set risk threshold to 2%"       → updates RiskAgent policy
  "Show audit log last 24h"        → queries SQLite, returns summary
  ```
- [ ] synopsis pattern wired for new data source ingestion

### Milestone
> Hyper-Sentinel proposes its own capability expansions. Operator approves. System grows its own skills.

---

## Phase 5 — Production Hardening & 24/7 Deployment
**Timeline: Weeks 7–8 | Goal: Always-on on the PC**

### Tasks
- [ ] Migrate Docker Compose → Upsonic AgentOS (Kubernetes) on PC
- [ ] NATS cluster mode — 3-node for high availability
- [ ] Postgres replaces SQLite for agent memory at scale
- [ ] Metrics dashboard: LLM cost per agent, token usage, decision latency
- [ ] Alert routing: risk/compliance events → mobile via OpenClaw
- [ ] PC = always-on deployment target; Mac = dev environment
- [ ] Backup and restore procedures for agent state
- [ ] Rate limiting and cost controls per agent

### Milestone
> Hyper-Sentinel running 24/7 on the PC, surviving reboots, alerting on mobile, generating daily intel reports, managing costs autonomously.

---

## Full Stack Reference

| Component | Technology |
|-----------|-----------|
| Agent Framework | Upsonic (Python, MIT) + Agno |
| Message Fabric | NATS.io + JetStream |
| Swarm Pattern | tobalo/agentic-osint (forked) |
| Worker Pattern | tobalo/gogent (forked) |
| Data Ingestion | tobalo/synopsis (forked) |
| Primary LLM | Anthropic Claude Sonnet |
| Secondary LLMs | Gemini (data), Grok (speed) |
| Local LLM | Ollama (dev/testing) |
| IDE | Antigravity (Cursor fork) |
| Governance | Upsonic Safety Engine + azdhril/Sentinel |
| Operator Interface | OpenClaw (Telegram/Discord) |
| Containers | Docker Compose → AgentOS |
| Storage | SQLite → Postgres → Oracle 23ai |
| Dev Machine | MacBook Pro |
| Deploy Machine | PC (Ryzen 7600X, 12GB GPU, 16GB RAM) |
