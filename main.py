"""
Hyper-Sentinel v3 — Interactive Terminal
==========================================
Run with: uv run main.py

Interactive REPL with NATS subscriber in background.
Solo mode: single MarketAgent (default)
Swarm mode: 5-agent Agno Team (Captain, Analyst, Trader, Risk Mgr, Ops)
"""

import asyncio
import os
import sys
import threading

# Add agent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents", "market-agent"))
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

# ── Suppress noisy debug logs — keep terminal clean ──────────────────
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("upsonic").setLevel(logging.WARNING)
logging.getLogger("upsonic.sentry.pipeline").setLevel(logging.WARNING)
logging.getLogger("agent").setLevel(logging.ERROR)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box


# ════════════════════════════════════════════════════════════════
# THEME + CONSOLE
# ════════════════════════════════════════════════════════════════

console = Console()

BANNER = """
[bold cyan]██╗  ██╗██╗   ██╗██████╗ ███████╗██████╗[/]
[bold cyan]██║  ██║╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗[/]
[bold cyan]███████║ ╚████╔╝ ██████╔╝█████╗  ██████╔╝[/]
[bold cyan]██╔══██║  ╚██╔╝  ██╔═══╝ ██╔══╝  ██╔══██╗[/]
[bold cyan]██║  ██║   ██║   ██║     ███████╗██║  ██║[/]
[bold cyan]╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝[/]

[bold white]S E N T I N E L   v 3[/]
[dim]Autonomous AI Agent Swarm · NATS · JetStream · Zero-Trust[/]
"""


# ════════════════════════════════════════════════════════════════
# AUTO-DETECT PROVIDER FROM KEY PREFIX
# ════════════════════════════════════════════════════════════════

KEY_PREFIXES = {
    "sk-ant-":  ("CLAUDE",  "Anthropic (Claude)",  "🟣"),
    "AIza":     ("GEMINI",  "Google (Gemini)",     "🔵"),
    "xai-":     ("GROK",    "xAI (Grok)",          "⚫"),
}


def _detect_provider(key: str):
    """Detect LLM provider from API key prefix. Returns (provider, label, emoji) or None."""
    for prefix, info in KEY_PREFIXES.items():
        if key.startswith(prefix):
            return info
    return None


def _save_to_env(key: str, value: str):
    """Save a key=value to .env, creating or updating as needed."""
    from pathlib import Path
    env_path = Path(__file__).resolve().parent / ".env"
    lines = []
    found = False
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith(f"{key}="):
                lines.append(f"{key}={value}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines) + "\n")
    os.environ[key] = value


def _has_llm_key() -> bool:
    """Check if LLM_API_KEY is configured."""
    val = os.getenv("LLM_API_KEY", "").strip()
    if val and val != "your-api-key-here":
        return True
    return False


def first_run_setup():
    """
    Interactive setup on first run — ported from v1.
    Step 1: AI provider key (required — auto-detected from prefix)
    Step 2: Hyperliquid wallet/key (optional)
    Then shows how to add more APIs.
    """
    console.print()
    welcome = Text()
    welcome.append("Welcome to Hyper Sentinel v3!\n", style="bold cyan")
    welcome.append("Let's get you set up. This only happens once — your keys are saved to .env automatically.", style="dim")
    console.print(Panel(welcome, border_style="cyan", padding=(1, 3)))
    console.print()

    # ── Step 1: AI Provider Key (required) ──────────────────
    step1 = Text()
    step1.append("Step 1 — AI Provider ", style="bold white")
    step1.append("(required)", style="bold yellow")
    console.print(Panel(step1, border_style="cyan", box=box.HORIZONTALS))

    console.print("  Paste any API key from a supported provider:\n")
    console.print("    [dim]•[/] [bold]Anthropic (Claude)[/]  [dim]→ console.anthropic.com[/]")
    console.print("    [dim]•[/] [bold]Google (Gemini)[/]     [dim]→ aistudio.google.com[/]")
    console.print("    [dim]•[/] [bold]xAI (Grok)[/]          [dim]→ console.x.ai[/]")
    console.print("    [dim]•[/] [bold]Ollama (local)[/]       [dim]→ no key needed, type 'ollama'[/]")
    console.print()

    while True:
        key = console.input("  [bold cyan]Paste your AI API key:[/] ").strip()

        if key.lower() == "ollama":
            _save_to_env("LLM_PROVIDER", "OLLAMA")
            _save_to_env("LLM_API_KEY", "local")
            console.print("\n  [green]✓ Ollama selected[/] — make sure ollama is running locally.")
            console.print("  [dim]Saved to .env — you won't be asked again.[/]\n")
            break

        if not key:
            console.print("  [red]No key entered. You need at least one AI provider key.[/]\n")
            continue

        detected = _detect_provider(key)
        if detected:
            provider, label, emoji = detected
            _save_to_env("LLM_PROVIDER", provider)
            _save_to_env("LLM_API_KEY", key)
            console.print(f"\n  [green]✓ Detected: {emoji} {label}[/]")
            console.print("  [dim]Saved to .env — you won't be asked again.[/]\n")
            break
        else:
            # Unknown prefix — save anyway with CLAUDE as default
            _save_to_env("LLM_PROVIDER", "CLAUDE")
            _save_to_env("LLM_API_KEY", key)
            console.print("\n  [yellow]⚠ Couldn't detect provider — defaulting to Claude.[/]")
            console.print("  [dim]Edit LLM_PROVIDER in .env if this is wrong.[/]\n")
            break

    # ── Step 2: Hyperliquid (optional) ──────────────────────
    step2 = Text()
    step2.append("Step 2 — Hyperliquid DEX ", style="bold white")
    step2.append("(optional)", style="dim")
    console.print(Panel(step2, border_style="cyan", box=box.HORIZONTALS))

    console.print("  [dim]For live trading on Hyperliquid perpetual futures.[/]")
    console.print("  [dim]Get started at: app.hyperliquid.xyz[/]")
    console.print("  [dim]Press Enter to skip — you can add it anytime with 'add hl'.[/]")
    console.print()

    hl_wallet = console.input("  [bold]Wallet address (0x...):[/] ").strip()
    if hl_wallet:
        _save_to_env("HYPERLIQUID_WALLET_ADDRESS", hl_wallet)
        console.print("  [green]✓ Wallet saved[/] — read-only account info enabled.")

        hl_key = console.input("\n  [bold]Private key for trading[/] [dim](Enter to skip for read-only)[/]: ").strip()
        if hl_key:
            _save_to_env("HYPERLIQUID_PRIVATE_KEY", hl_key)
            console.print("  [green]✓ Trading enabled[/]\n")
        else:
            console.print("  [dim]Read-only mode — type 'add hl' later to enable trading.[/]\n")
    else:
        console.print("  [dim]Skipped — type 'add hl' anytime to configure.[/]\n")

    # ── Done — show how to add more APIs ────────────────────
    cmds = Table(show_header=False, box=None, padding=(0, 1))
    cmds.add_column("Command", style="bold cyan")
    cmds.add_column("Description", style="dim")
    cmds.add_row("add y2", "Y2 news sentiment + AI recaps + reports")
    cmds.add_row("add x", "X (Twitter) tweets, trends & sentiment")
    cmds.add_row("add elfa", "Elfa AI trending tokens + social mentions")
    cmds.add_row("add hl", "Hyperliquid DEX trading")
    cmds.add_row("add aster", "Aster DEX futures trading")
    cmds.add_row("add polymarket", "Polymarket prediction markets")
    cmds.add_row("add fred", "FRED economic data (GDP, CPI, rates)")
    cmds.add_row("add telegram", "Telegram notifications")
    cmds.add_row("status", "Show all API connections")

    console.print(Panel(cmds, title="[green]✓ Setup complete![/]", title_align="left", border_style="green", padding=(1, 2)))
    console.print()

    # Reload env
    load_dotenv(override=True)


def _bridge_api_keys():
    """
    Bridge LLM_API_KEY → provider-specific env vars.

    Upsonic expects ANTHROPIC_API_KEY, GOOGLE_API_KEY, etc.
    Agno expects ANTHROPIC_API_KEY, GEMINI_API_KEY, XAI_API_KEY, etc.
    This function sets ALL of them from our single LLM_API_KEY so every
    agent framework works regardless of which one is active.
    """
    api_key = os.getenv("LLM_API_KEY", "").strip()
    provider = os.getenv("LLM_PROVIDER", "CLAUDE").upper()

    if not api_key or api_key == "your-api-key-here":
        return

    # Map provider → all env vars each framework might check
    BRIDGE_MAP = {
        "CLAUDE": [
            "ANTHROPIC_API_KEY",
        ],
        "GEMINI": [
            "GOOGLE_API_KEY",      # Upsonic uses this
            "GEMINI_API_KEY",      # Agno uses this
        ],
        "GROK": [
            "XAI_API_KEY",         # Both Upsonic and Agno
        ],
    }

    env_vars = BRIDGE_MAP.get(provider, [])
    for var in env_vars:
        if not os.getenv(var):
            os.environ[var] = api_key

    # Gemini needs the endpoint set for Agno (OpenAI-compatible)
    if provider == "GEMINI":
        if not os.getenv("GEMINI_BASE_URL"):
            os.environ["GEMINI_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"


def _validate_model_config():
    """
    Validate LLM config at startup — catch misconfigs before agents fail.
    Returns (provider, model_string) or raises with clear error.
    """
    provider = os.getenv("LLM_PROVIDER", "CLAUDE").upper()
    api_key = os.getenv("LLM_API_KEY", "").strip()

    VALID_PROVIDERS = {"CLAUDE", "GEMINI", "GROK", "OLLAMA"}
    if provider not in VALID_PROVIDERS:
        console.print(f"  [red]✗ Unknown LLM_PROVIDER: '{provider}'[/]")
        console.print(f"  [dim]Valid options: {', '.join(sorted(VALID_PROVIDERS))}[/]")
        console.print(f"  [dim]Edit LLM_PROVIDER in .env[/]\n")
        return False

    if provider != "OLLAMA" and (not api_key or api_key == "your-api-key-here"):
        console.print(f"  [red]✗ LLM_API_KEY is empty for provider {provider}[/]")
        console.print(f"  [dim]Run again to set up or edit .env manually.[/]\n")
        return False

    # Gemini-specific: validate key prefix
    if provider == "GEMINI" and not api_key.startswith("AIza"):
        console.print(f"  [yellow]⚠ Gemini key doesn't start with 'AIza' — may not work.[/]")
        console.print(f"  [dim]Get a valid key at: aistudio.google.com[/]\n")

    # Provider → model mapping (for display)
    MODEL_MAP = {
        "CLAUDE": "anthropic/claude-sonnet-4-5",
        "GEMINI": "google/gemini-2.0-flash",
        "GROK": "xai/grok-2",
        "OLLAMA": "ollama/deepseek-r1:1.5b",
    }
    custom_model = os.getenv("LLM_MODEL", "").strip()
    model = custom_model if custom_model else MODEL_MAP.get(provider, "unknown")

    console.print(f"  [green]✓ LLM:[/] {provider} → [bold]{model}[/]")
    return True


# ════════════════════════════════════════════════════════════════
# DATA SOURCE DETECTION
# ════════════════════════════════════════════════════════════════

def _check_data_sources() -> list[dict]:
    """Check which data sources are available based on .env keys."""
    sources = [
        {"name": "CoinGecko",     "icon": "🪙", "key": None,                   "desc": "10,000+ crypto prices + top N + search"},
        {"name": "YFinance",      "icon": "📈", "key": None,                   "desc": "stocks + ETFs + analyst recs + news"},
        {"name": "FRED",          "icon": "🏛️", "key": "FRED_API_KEY",          "desc": "GDP, CPI, rates, yield curve, VIX"},
        {"name": "Y2 Intelligence","icon": "📰", "key": "Y2_API_KEY",           "desc": "news sentiment + recaps + reports"},
        {"name": "Elfa AI",       "icon": "🔮", "key": "ELFA_API_KEY",         "desc": "trending tokens + social mentions"},
        {"name": "X (Twitter)",   "icon": "🐦", "key": "X_BEARER_TOKEN",       "desc": "tweets + trends + sentiment"},
        {"name": "Hyperliquid",   "icon": "⚡", "key": "HYPERLIQUID_PRIVATE_KEY","desc": "perp futures + orders + positions"},
        {"name": "Aster DEX",     "icon": "🌟", "key": "ASTER_API_KEY",        "desc": "futures + orderbook + klines + leverage"},
        {"name": "Polymarket",    "icon": "🎲", "key": "POLYMARKET_PRIVATE_KEY","desc": "browse + bet + positions + orders"},
        {"name": "TradingView",   "icon": "📺", "key": "WEBHOOK_SECRET",       "desc": f"port {os.getenv('WEBHOOK_PORT', '8888')} · receives TV alerts"},
    ]
    for s in sources:
        if s["key"] is None:
            s["status"] = "available"
        elif os.getenv(s["key"], ""):
            s["status"] = "connected"
        else:
            s["status"] = "not_configured"
    return sources


# ════════════════════════════════════════════════════════════════
# STATUS DASHBOARD
# ════════════════════════════════════════════════════════════════

def _print_status(nats_connected=False, decisions_logged=0, mode="solo"):
    """Show infrastructure, data sources, and agent status."""
    # ── Infrastructure ──
    infra = Table(
        title="[bold cyan]📡 Infrastructure[/]", title_justify="left",
        show_header=False, box=box.SIMPLE_HEAVY, border_style="cyan",
        padding=(0, 2), expand=False,
    )
    infra.add_column("Component", style="bold white", min_width=18)
    infra.add_column("Status", min_width=16)
    infra.add_column("Details", style="dim")

    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    if nats_connected:
        infra.add_row("⚡ NATS", "[green]● Connected[/]", nats_url)
    else:
        infra.add_row("⚡ NATS", "[yellow]○ Connecting...[/]", nats_url)

    provider = os.getenv("LLM_PROVIDER", "CLAUDE")
    api_key = os.getenv("LLM_API_KEY", "")
    if api_key:
        infra.add_row("🤖 LLM", f"[green]● {provider}[/]", "Ready")
    else:
        infra.add_row("🤖 LLM", "[red]✗ No API key[/]", "Edit .env")

    infra.add_row("🗄️  SQLite", "[green]● Active[/]", f"{decisions_logged} decisions logged")

    if nats_connected:
        infra.add_row("📦 JetStream", "[green]● SENTINEL_STREAM[/]", "7-day retention")
    else:
        infra.add_row("📦 JetStream", "[dim]○ Waiting for NATS[/]", "")

    # REST API status
    if api_status.get("running"):
        api_port = api_status.get("port", 8000)
        infra.add_row("🌐 REST API", f"[green]● http://localhost:{api_port}/docs[/]", f"{api_status.get('tools', '?')} tools")
    elif api_status.get("disabled"):
        infra.add_row("🌐 REST API", "[dim]○ Disabled[/]", "API_ENABLED=false")
    else:
        infra.add_row("🌐 REST API", "[yellow]○ Not started[/]", "")

    console.print()
    console.print(infra)

    # ── Data Sources ──
    sources = _check_data_sources()

    # Map service aliases → data source display names for highlighting
    _SERVICE_TO_SOURCE = {
        "fred": "FRED", "y2": "Y2 Intelligence", "elfa": "Elfa AI",
        "x": "X (Twitter)", "twitter": "X (Twitter)",
        "hl": "Hyperliquid", "hyperliquid": "Hyperliquid",
        "aster": "Aster DEX", "polymarket": "Polymarket",
        "telegram": "Telegram", "tradingview": "TradingView", "tv": "TradingView",
    }
    highlight_source = _SERVICE_TO_SOURCE.get(_last_configured_service, "") if _last_configured_service else ""

    ds = Table(
        title="[bold cyan]📊 Data Sources[/]", title_justify="left",
        show_header=False, box=box.SIMPLE_HEAVY, border_style="cyan",
        padding=(0, 2), expand=False,
    )
    ds.add_column("Source", style="bold white", min_width=18)
    ds.add_column("Status", min_width=20)
    ds.add_column("Details", style="dim")

    for s in sources:
        is_highlight = (s["name"] == highlight_source)
        marker = " ✨" if is_highlight else ""
        if s["status"] == "available":
            ds.add_row(f"{s['icon']} {s['name']}{marker}", "[green]● Always available[/]", s["desc"])
        elif s["status"] == "connected":
            trading = s["name"] in ("Hyperliquid", "Aster DEX", "Polymarket")
            label = "[bold green]● Trading enabled[/]" if trading else "[green]● Connected[/]"
            if s["name"] == "TradingView":
                label = "[green]● Webhook active[/]"
            if is_highlight:
                label = f"[bold green]● Just configured ✓[/]"
            ds.add_row(f"{s['icon']} {s['name']}{marker}", label, s["desc"])
        else:
            ds.add_row(f"{s['icon']} {s['name']}{marker}", "[dim]○ Not configured[/]", s["desc"])

    console.print(ds)

    # ── Agents ──
    agents = Table(
        title="[bold cyan]🛡️  Agents[/]", title_justify="left",
        show_header=False, box=box.SIMPLE_HEAVY, border_style="cyan",
        padding=(0, 2), expand=False,
    )
    agents.add_column("Agent", style="bold white", min_width=18)
    agents.add_column("Status", min_width=16)
    agents.add_column("Subject", style="dim")

    if mode == "swarm":
        agents.add_row("🎖️  Captain", "[green]● ACTIVE[/]", "routes queries to team")
        agents.add_row("📊 Analyst", "[green]● ACTIVE[/]", "CoinGecko + FRED + Y2 + Elfa + X")
        agents.add_row("💹 Trader", "[green]● ACTIVE[/]", "HL + Aster + Polymarket")
        agents.add_row("⚠️  Risk Manager", "[green]● ACTIVE[/]", "portfolio + sizing + risk")
        agents.add_row("⚙️  Ops", "[green]● ACTIVE[/]", "files + GitHub + Postgres")
    elif mode == "team":
        agents.add_row("📊 Analyst", "[green]● ACTIVE[/]", "crypto + macro + sentiment tools")
        agents.add_row("🛡️  RiskManager", "[green]● ACTIVE[/]", "ALL_TOOLS · guardrails")
        agents.add_row("⚡ Trader", "[green]● ACTIVE[/]", "HL + Aster + Polymarket")
        agents.add_row("🧠 Leader", "[cyan]● COORDINATING[/]", "routes tasks to specialists")
    else:
        if nats_connected:
            agents.add_row("📊 MarketAgent", "[green]● ONLINE[/]", "sentinel.market.data")
        else:
            agents.add_row("📊 MarketAgent", "[yellow]○ Starting...[/]", "sentinel.market.data")

    console.print(agents)

    # Mode indicator
    connected_count = sum(1 for s in sources if s["status"] in ("available", "connected"))
    mode_labels = {
        "swarm": "SWARM (5 Agno agents)",
        "team": "TEAM (3 Upsonic agents · coordinate)",
        "solo": "SOLO (MarketAgent)",
    }
    mode_label = mode_labels.get(mode, "SOLO (MarketAgent)")
    console.print(f"  [dim]{connected_count} data sources · Mode: [bold]{mode_label}[/][/]")


def _print_help(mode="solo"):
    """Show available commands."""
    cmds = Table(
        title="[bold cyan]Commands[/]", title_justify="left",
        show_header=False, box=box.SIMPLE_HEAVY, border_style="cyan",
        padding=(0, 2), expand=False,
    )
    cmds.add_column("Command", style="bold cyan", min_width=22)
    cmds.add_column("Description", style="dim")

    cmds.add_row("status", "Show infrastructure + agent status")
    cmds.add_row("logs [N]", "Show last N decisions from SQLite (default: 5)")
    cmds.add_row("scan <symbols>", "Trigger a market scan (e.g. scan SPY QQQ BTC-USD)")
    cmds.add_row("", "")
    cmds.add_row("[bold green]── Agent Modes ──[/]", "")
    cmds.add_row("solo", "Single MarketAgent (Upsonic)")
    cmds.add_row("swarm", "Agno 5-agent team (Captain + specialists)")
    cmds.add_row("team", "Upsonic Team (Analyst + RiskMgr + Trader)")
    cmds.add_row("", "")
    cmds.add_row("[bold green]── Autonomous ──[/]", "")
    cmds.add_row("sentinel", "Start autonomous monitoring loop (24/7)")
    cmds.add_row("sentinel stop", "Stop autonomous monitoring")
    cmds.add_row("guardrails", "Show trade limits + kill switch status")
    cmds.add_row("mission list", "Show active standing orders")
    cmds.add_row("mission add <desc>", "Create a new mission (e.g. 'alert if BTC < 80K')")
    cmds.add_row("", "")
    cmds.add_row("[bold green]── Browser ──[/]", "")
    cmds.add_row("open <site>", "Instant Chrome open (youtube, tradingview, etc.)")
    cmds.add_row("browse <task>", "LLM + Playwright browser automation (complex tasks)")
    cmds.add_row("", "")
    cmds.add_row("[bold green]── Configure ──[/]", "")
    cmds.add_row("add", "Show available data source integrations")
    cmds.add_row("add <service>", "Configure API key (hl, y2, elfa, fred, etc.)")
    cmds.add_row("", "")
    cmds.add_row("help", "Show this help")
    cmds.add_row("clear", "Clear screen and reprint banner")
    cmds.add_row("quit", "Shutdown and exit")
    cmds.add_row("", "")
    cmds.add_row("[italic]any question[/]", "[italic]Ask the active agent anything[/]")

    console.print()
    console.print(cmds)
    console.print()


# ════════════════════════════════════════════════════════════════
# NATS BACKGROUND SUBSCRIBER
# ════════════════════════════════════════════════════════════════

nats_status = {"connected": False, "decisions": 0}


def _start_nats_subscriber():
    """Start the NATS subscriber in a background thread."""
    import nats as nats_lib
    from nats.js.api import StreamConfig, RetentionPolicy
    from config import AgentConfig, STREAM_NAME, CONSUMER_NAME, SUBJECT_MARKET_DATA
    from db import DecisionLogger

    agent_config = AgentConfig()
    decision_logger = DecisionLogger(agent_config.db_path)
    nats_status["decisions"] = decision_logger.count()

    async def _run_subscriber():
        nc = await nats_lib.connect(
            agent_config.nats_url,
            name=agent_config.agent_name,
            max_reconnect_attempts=60,
            reconnect_time_wait=2,
        )
        nats_status["connected"] = True

        js = nc.jetstream()

        try:
            await js.find_stream_name_by_subject(SUBJECT_MARKET_DATA)
        except Exception:
            await js.add_stream(
                StreamConfig(
                    name=STREAM_NAME,
                    subjects=["sentinel.>"],
                    retention=RetentionPolicy.LIMITS,
                    max_msgs=100_000,
                    max_bytes=256 * 1024 * 1024,
                    max_age=7 * 24 * 60 * 60,
                    storage="file",
                    num_replicas=1,
                )
            )

        try:
            await js.delete_consumer(STREAM_NAME, CONSUMER_NAME)
        except Exception:
            pass

        from subscriber import _process_message

        async def message_handler(msg):
            await _process_message(msg, nc, js, decision_logger, agent_config)
            nats_status["decisions"] = decision_logger.count()

        await js.subscribe(
            SUBJECT_MARKET_DATA,
            durable=CONSUMER_NAME,
            stream=STREAM_NAME,
            cb=message_handler,
        )

        while True:
            await asyncio.sleep(1)

    def _thread_target():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_run_subscriber())
        except Exception:
            nats_status["connected"] = False

    thread = threading.Thread(target=_thread_target, daemon=True)
    thread.start()


# ════════════════════════════════════════════════════════════════
# REST API — Auto-start as background thread
# ════════════════════════════════════════════════════════════════

api_status = {"running": False, "disabled": False, "port": 8000, "tools": 0}


def _start_api_server():
    """Start the REST API server as a daemon thread (same pattern as sentinel.py)."""
    api_enabled = os.getenv("API_ENABLED", "true").lower() == "true"
    if not api_enabled:
        api_status["disabled"] = True
        return

    try:
        from api.server import create_app, registry, API_PORT, API_HOST
        import uvicorn

        app = create_app()
        api_status["port"] = API_PORT
        api_status["tools"] = registry.tool_count

        def _run_api():
            uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="warning")

        api_thread = threading.Thread(target=_run_api, daemon=True)
        api_thread.start()
        api_status["running"] = True
    except Exception as e:
        logging.getLogger("sentinel").warning(f"REST API failed to start: {e}")
        api_status["running"] = False


# ════════════════════════════════════════════════════════════════
# ADD COMMAND — Interactive API key configuration
# ════════════════════════════════════════════════════════════════

# Map of service aliases to their env vars and descriptions
_ADD_SERVICES = {
    "fred":       {"keys": [("FRED_API_KEY", "FRED API key")], "name": "FRED Economic Data", "url": "https://fred.stlouisfed.org/docs/api/api_key.html"},
    "y2":         {"keys": [("Y2_API_KEY", "Y2 Intelligence API key")], "name":"Y2 Intelligence", "url": "https://y2.finance"},
    "elfa":       {"keys": [("ELFA_API_KEY", "Elfa AI API key")], "name": "Elfa AI", "url": "https://elfa.ai"},
    "x":          {"keys": [("X_BEARER_TOKEN", "X (Twitter) Bearer token")], "name": "X (Twitter)", "url": "https://developer.x.com"},
    "twitter":    {"keys": [("X_BEARER_TOKEN", "X (Twitter) Bearer token")], "name": "X (Twitter)", "url": "https://developer.x.com"},
    "hl":         {"keys": [("HYPERLIQUID_WALLET_ADDRESS", "Wallet address"), ("HYPERLIQUID_PRIVATE_KEY", "Private key")], "name": "Hyperliquid", "url": "https://app.hyperliquid.xyz"},
    "hyperliquid":{"keys": [("HYPERLIQUID_WALLET_ADDRESS", "Wallet address"), ("HYPERLIQUID_PRIVATE_KEY", "Private key")], "name": "Hyperliquid", "url": "https://app.hyperliquid.xyz"},
    "aster":      {"keys": [("ASTER_API_KEY", "Aster API key"), ("ASTER_API_SECRET", "Aster secret key")], "name": "Aster DEX", "url": "https://www.asterdex.com"},
    "polymarket": {"keys": [("POLYMARKET_PRIVATE_KEY", "Polymarket private key")], "name": "Polymarket", "url": "https://polymarket.com"},
    "telegram":   {"keys": [("TELEGRAM_BOT_TOKEN", "Bot token (from @BotFather)"), ("TELEGRAM_CHAT_ID", "Chat ID")], "name": "Telegram", "url": "https://t.me/BotFather"},
    "tradingview":{"keys": [("WEBHOOK_SECRET", "Webhook secret (any string)")], "name": "TradingView Webhooks", "url": "https://www.tradingview.com/support/solutions/43000529348"},
    "tv":         {"keys": [("WEBHOOK_SECRET", "Webhook secret (any string)")], "name": "TradingView Webhooks", "url": "https://www.tradingview.com/support/solutions/43000529348"},
    "api":        {"keys": [("API_KEYS", "API key for REST access (e.g. sk-your-key)")], "name": "REST API Auth", "url": "http://localhost:8000/docs"},
}

# Track the last configured service for status highlighting
_last_configured_service = None


# ════════════════════════════════════════════════════════════════
# PER-SERVICE VERIFY FUNCTIONS — lightweight, non-destructive
# ════════════════════════════════════════════════════════════════

def _verify_fred() -> dict:
    """Verify FRED API key by fetching a single series."""
    import requests as _req
    key = os.getenv("FRED_API_KEY", "").strip()
    if not key:
        return {"ok": False, "error": "FRED_API_KEY not set"}
    try:
        r = _req.get(
            "https://api.stlouisfed.org/fred/series",
            params={"api_key": key, "series_id": "GDP", "file_type": "json"},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            title = data.get("seriess", [{}])[0].get("title", "")
            return {"ok": True, "detail": f"Fetched series: {title}"}
        return {"ok": False, "error": f"HTTP {r.status_code}", "hint": "Check your FRED API key"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _verify_y2() -> dict:
    """Verify Y2 Intelligence key by listing 1 news item."""
    try:
        from y2 import Y2
    except ImportError:
        return {"ok": False, "error": "y2-py not installed (run: uv add y2-py)"}
    key = os.getenv("Y2_API_KEY", "").strip()
    if not key:
        return {"ok": False, "error": "Y2_API_KEY not set"}
    try:
        client = Y2(api_key=key)
        news = client.news.list(topics="bitcoin", limit=1)
        return {"ok": True, "detail": f"Connected — {len(news.data)} item(s) returned"}
    except Exception as e:
        return {"ok": False, "error": str(e), "hint": "Check key at y2.dev/app/developers/api-keys"}


def _verify_elfa() -> dict:
    """Verify Elfa AI key by fetching 1 trending token."""
    import requests as _req
    key = os.getenv("ELFA_API_KEY", "").strip()
    if not key:
        return {"ok": False, "error": "ELFA_API_KEY not set"}
    try:
        r = _req.get(
            "https://api.elfa.ai/v2/aggregations/trending-tokens",
            headers={"x-elfa-api-key": key, "Accept": "application/json"},
            params={"timeWindow": "24h", "limit": 1},
            timeout=10,
        )
        if r.status_code == 200:
            return {"ok": True, "detail": "Trending tokens endpoint OK"}
        return {"ok": False, "error": f"HTTP {r.status_code}", "hint": "Check your Elfa API key"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _verify_x() -> dict:
    """Verify X (Twitter) Bearer token with a small search."""
    import requests as _req
    token = os.getenv("X_BEARER_TOKEN", "").strip()
    if not token:
        return {"ok": False, "error": "X_BEARER_TOKEN not set"}
    try:
        r = _req.get(
            "https://api.twitter.com/2/tweets/search/recent",
            headers={"Authorization": f"Bearer {token}"},
            params={"query": "crypto", "max_results": 10},
            timeout=10,
        )
        if r.status_code == 200:
            count = len(r.json().get("data", []))
            return {"ok": True, "detail": f"Search OK — {count} tweet(s) returned"}
        elif r.status_code == 401:
            return {"ok": False, "error": "401 Unauthorized", "hint": "Bearer token is invalid or expired"}
        elif r.status_code == 403:
            return {"ok": False, "error": "403 Forbidden", "hint": "Token lacks search permissions — check your X app settings"}
        return {"ok": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _verify_hl() -> dict:
    """Verify Hyperliquid connection using existing get_hl_config."""
    try:
        from scrapers.hyperliquid_scraper import get_hl_config
        config = get_hl_config()
        conn = config.get("connection", "")
        if conn == "Connected":
            value = config.get("account_value", "0")
            mode = config.get("mode", "Unknown")
            return {"ok": True, "detail": f"{mode} — account value: ${value}"}
        elif "Error" in conn:
            return {"ok": False, "error": conn}
        elif config.get("wallet_address") == "Not configured":
            return {"ok": False, "error": "Wallet address not configured"}
        return {"ok": True, "detail": f"Mode: {config.get('mode', 'Unknown')}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _verify_aster() -> dict:
    """Verify Aster DEX using existing aster_diagnose."""
    try:
        from scrapers.aster_scraper import aster_diagnose
        diag = aster_diagnose()
        overall = diag.get("overall", "")
        if "✅" in overall:
            results = []
            if "✅" in diag.get("connectivity", ""):
                results.append("connectivity")
            if "✅" in diag.get("get_auth", ""):
                results.append("read access")
            if "✅" in diag.get("post_auth", ""):
                results.append("trade access")
            return {"ok": True, "detail": f"Operational — {', '.join(results)} confirmed"}
        elif "⚠️" in overall:
            return {"ok": True, "detail": overall.replace("⚠️ ", ""), "warning": True}
        else:
            hint = diag.get("get_auth_hint") or diag.get("post_auth_hint") or diag.get("hint", "")
            return {"ok": False, "error": overall.replace("❌ ", ""), "hint": hint}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _verify_polymarket() -> dict:
    """Verify Polymarket — ping Gamma API + test CLOB client if key set."""
    import requests as _req
    # Public read — always works if internet is up
    try:
        r = _req.get(
            "https://gamma-api.polymarket.com/markets",
            params={"limit": 1, "active": "true"},
            timeout=15,
        )
        if r.status_code != 200:
            return {"ok": False, "error": f"Gamma API returned HTTP {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": f"Cannot reach Polymarket: {e}"}

    # If private key is set, test CLOB client auth
    pk = os.getenv("POLYMARKET_PRIVATE_KEY", "").strip()
    if pk:
        try:
            from scrapers.polymarket_scraper import _get_clob_client
            client = _get_clob_client()
            if client:
                return {"ok": True, "detail": "Markets API + trading auth OK"}
            return {"ok": False, "error": "CLOB client init failed", "hint": "Check private key format"}
        except Exception as e:
            return {"ok": False, "error": f"CLOB auth error: {e}"}

    return {"ok": True, "detail": "Markets API OK (read-only — no trading key)"}


def _verify_telegram() -> dict:
    """Verify Telegram bot token via getMe API."""
    import requests as _req
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN not set"}
    try:
        r = _req.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("ok"):
                bot_name = data.get("result", {}).get("username", "unknown")
                return {"ok": True, "detail": f"Bot @{bot_name} authenticated"}
        return {"ok": False, "error": f"HTTP {r.status_code}", "hint": "Check bot token from @BotFather"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _verify_tradingview() -> dict:
    """TradingView webhooks — no remote API to ping, just confirm secret is set."""
    secret = os.getenv("WEBHOOK_SECRET", "").strip()
    if secret:
        port = os.getenv("WEBHOOK_PORT", "8888")
        return {"ok": True, "detail": f"Webhook secret set — listening on port {port}"}
    return {"ok": False, "error": "WEBHOOK_SECRET not set"}


# Service name → verify function mapping
_VERIFY_MAP = {
    "fred": _verify_fred,
    "y2": _verify_y2,
    "elfa": _verify_elfa,
    "x": _verify_x,
    "twitter": _verify_x,
    "hl": _verify_hl,
    "hyperliquid": _verify_hl,
    "aster": _verify_aster,
    "polymarket": _verify_polymarket,
    "telegram": _verify_telegram,
    "tradingview": _verify_tradingview,
    "tv": _verify_tradingview,
}


def _verify_service(service: str, service_name: str):
    """Run verification for a service and print Rich-formatted results."""
    verify_fn = _VERIFY_MAP.get(service)
    if not verify_fn:
        console.print(f"  [dim]No auto-verify available for {service_name}.[/]\n")
        return

    console.print(f"\n  [bold cyan]🔍 Verifying {service_name}...[/]")

    try:
        with console.status(f"[cyan]Testing {service_name} connection...[/]"):
            result = verify_fn()
    except Exception as e:
        result = {"ok": False, "error": str(e)}

    if result.get("ok"):
        if result.get("warning"):
            console.print(f"  [yellow]⚠️  {result.get('detail', 'Partially working')}[/]")
        else:
            console.print(f"  [green]✅ {result.get('detail', 'Connected')}[/]")
        console.print(f"  [green]✓ {service_name} is live![/]\n")
    else:
        console.print(f"  [red]❌ {result.get('error', 'Verification failed')}[/]")
        if result.get("hint"):
            console.print(f"  [yellow]💡 Hint: {result['hint']}[/]")
        console.print(f"  [yellow]⚠ Keys saved but verification failed. Double-check credentials.[/]\n")


def _handle_add(service: str):
    """Interactively configure an API key for a data source."""
    global _last_configured_service
    service = service.lower().strip()

    if not service or service == "list":
        # Show available add commands
        tbl = Table(show_header=False, box=None, padding=(0, 1))
        tbl.add_column("Command", style="bold cyan")
        tbl.add_column("Description", style="dim")
        tbl.add_row("add y2", "Y2 news sentiment + AI recaps + reports")
        tbl.add_row("add x", "X (Twitter) tweets, trends & sentiment")
        tbl.add_row("add elfa", "Elfa AI trending tokens + social mentions")
        tbl.add_row("add hl", "Hyperliquid DEX trading")
        tbl.add_row("add aster", "Aster DEX futures trading")
        tbl.add_row("add polymarket", "Polymarket prediction markets")
        tbl.add_row("add fred", "FRED economic data (GDP, CPI, rates)")
        tbl.add_row("add telegram", "Telegram notifications")
        tbl.add_row("add tv", "TradingView webhook alerts")
        console.print(Panel(tbl, title="[cyan]Available Integrations[/]", border_style="cyan", padding=(1, 2)))
        return

    if service not in _ADD_SERVICES:
        console.print(f"  [red]Unknown service: {service}[/]")
        console.print(f"  [dim]Type 'add' to see available integrations.[/]\n")
        return

    svc = _ADD_SERVICES[service]
    console.print(f"\n  [bold cyan]🔧 Configure {svc['name']}[/]")
    console.print(f"  [dim]Get keys at: {svc['url']}[/]\n")

    all_saved = True
    for env_var, label in svc["keys"]:
        current = os.getenv(env_var, "")
        if current:
            mask = current[:4] + "..." + current[-4:] if len(current) > 8 else "****"
            console.print(f"  [green]✓[/] {label}: [dim]{mask}[/] (already set)")
            overwrite = console.input(f"  [dim]Overwrite? (y/N):[/] ").strip().lower()
            if overwrite != "y":
                continue

        value = console.input(f"  [cyan]{label}:[/] ").strip()
        if value:
            _save_to_env(env_var, value)
            os.environ[env_var] = value
            console.print(f"  [green]✓ Saved[/]")
        else:
            console.print(f"  [yellow]Skipped[/]")
            all_saved = False

    # Reload dotenv
    load_dotenv(override=True)

    if all_saved:
        _last_configured_service = service
        _verify_service(service, svc["name"])
    else:
        console.print(f"\n  [yellow]Partially configured.[/] Type 'add {service}' to finish.\n")


# ════════════════════════════════════════════════════════════════
# AGENT CHAT — Solo + Swarm + Team
# ════════════════════════════════════════════════════════════════

swarm_instance = None
team_instance = None
sentinel_instance = None
sentinel_thread = None


def _md_to_rich(text: str) -> str:
    """Convert markdown formatting to Rich markup for clean terminal output."""
    import re
    # Convert **bold** to [bold]...[/bold]
    text = re.sub(r'\*\*(.+?)\*\*', r'[bold]\1[/bold]', text)
    # Convert ## headers to bold cyan
    text = re.sub(r'^## (.+)$', r'[bold cyan]\1[/bold cyan]', text, flags=re.MULTILINE)
    # Convert # headers to bold
    text = re.sub(r'^# (.+)$', r'[bold white]\1[/bold white]', text, flags=re.MULTILINE)
    return text


def _chat_solo(user_input: str):
    """Send a question to the MarketAgent (solo mode)."""
    from agent import analyze_market_chat

    console.print()
    with console.status("[cyan]MarketAgent thinking...[/]"):
        try:
            response = analyze_market_chat(user_input)
            rich_response = _md_to_rich(str(response))
            console.print(Panel(
                rich_response,
                title="[bold cyan]🛡️ Sentinel[/]",
                border_style="cyan",
                padding=(1, 2),
            ))
            console.print()
        except Exception as e:
            console.print(f"  [red]Error: {e}[/]\n")


def _chat_swarm(user_input: str):
    """Send a question to the Agno swarm team."""
    global swarm_instance

    console.print()
    with console.status("[cyan]Swarm processing...[/]"):
        try:
            if swarm_instance is None:
                from agents.swarm import SwarmAgent
                swarm_instance = SwarmAgent()
            response = swarm_instance.chat(user_input)
            console.print(f"  [bold cyan]🛡️  Swarm →[/] {response}\n")
        except Exception as e:
            console.print(f"  [red]Swarm error: {e}[/]\n")


def _chat_team(user_input: str):
    """Send a question to the Upsonic Team."""
    global team_instance

    console.print()
    with console.status("[cyan]Team processing...[/]"):
        try:
            if team_instance is None:
                from agents.team import build_team
                team_instance = build_team()
            from agents.team import team_chat
            response = team_chat(team_instance, user_input)
            console.print(f"  [bold green]🛡️  Team →[/] {response}\n")
        except Exception as e:
            console.print(f"  [red]Team error: {e}[/]\n")


def _start_sentinel():
    """Start the Sentinel autonomous loop in a background thread."""
    global sentinel_instance, sentinel_thread

    if sentinel_thread and sentinel_thread.is_alive():
        console.print("  [yellow]Sentinel is already running.[/]")
        return

    def _run():
        from core.sentinel import Sentinel
        sentinel_instance = Sentinel()
        sentinel_instance.run()

    sentinel_thread = threading.Thread(target=_run, daemon=True)
    sentinel_thread.start()
    console.print("  [bold green]🛡️ Sentinel autonomous loop started![/]")
    console.print("  [dim]Monitors running in background. Type 'sentinel stop' to halt.[/]\n")


def _stop_sentinel():
    """Stop the Sentinel autonomous loop."""
    global sentinel_instance, sentinel_thread
    if sentinel_instance and hasattr(sentinel_instance, 'scheduler'):
        try:
            sentinel_instance.scheduler.stop()
        except Exception:
            pass
    sentinel_instance = None
    sentinel_thread = None
    console.print("  [yellow]Sentinel autonomous loop stopped.[/]\n")


def _show_guardrails():
    """Show current guardrail status."""
    from core.sentinel import Guardrails
    g = Guardrails()
    status = g.status()

    tbl = Table(
        title="[bold cyan]🛡️ Guardrails[/]", title_justify="left",
        show_header=False, box=box.SIMPLE_HEAVY, border_style="cyan",
        padding=(0, 2),
    )
    tbl.add_column("Setting", style="bold")
    tbl.add_column("Value")
    for k, v in status.items():
        tbl.add_row(k.replace("_", " ").title(), str(v))
    console.print()
    console.print(tbl)
    console.print()


def _handle_mission(cmd_parts: list[str]):
    """Handle mission sub-commands."""
    if len(cmd_parts) < 2:
        console.print("  [yellow]Usage: mission list | mission add <description>[/]\n")
        return

    subcmd = cmd_parts[1]

    try:
        from core.missions import MissionController
        mc = MissionController()
    except Exception as e:
        console.print(f"  [red]Mission system unavailable: {e}[/]\n")
        return

    if subcmd == "list":
        missions = mc.list_missions()
        if not missions:
            console.print("  [dim]No missions configured.[/]\n")
            return
        tbl = Table(
            title="[bold cyan]📋 Missions[/]", title_justify="left",
            box=box.SIMPLE_HEAVY, border_style="cyan",
        )
        tbl.add_column("Name", style="bold")
        tbl.add_column("Status")
        tbl.add_column("Interval")
        tbl.add_column("Runs", justify="right")
        tbl.add_column("Last Run", style="dim")
        for m in missions:
            status = "[green]active[/]" if m.active else "[yellow]paused[/]"
            tbl.add_row(
                m.name,
                status,
                f"{m.interval_minutes}m",
                str(m.run_count),
                (m.last_run or "never")[:19],
            )
        console.print()
        console.print(tbl)
        console.print()

    elif subcmd == "add" and len(cmd_parts) > 2:
        desc = " ".join(cmd_parts[2:])
        mission = mc.create_mission(
            template_key="custom",
            params={"description": desc},
        )
        if mission:
            console.print(f"  [green]✓ Mission created:[/] {mission.name}\n")
        else:
            console.print(f"  [red]Failed to create mission.[/]\n")
    else:
        console.print("  [yellow]Usage: mission list | mission add <description>[/]\n")


def _show_logs(n: int = 5):
    """Show last N decisions from SQLite."""
    from config import AgentConfig
    from db import DecisionLogger

    agent_config = AgentConfig()
    logger = DecisionLogger(agent_config.db_path)
    decisions = logger.get_recent(n)

    if not decisions:
        console.print("\n  [dim]No decisions logged yet.[/]\n")
        return

    tbl = Table(
        title=f"[bold cyan]Last {len(decisions)} Decisions[/]",
        box=box.SIMPLE_HEAVY, border_style="cyan",
    )
    tbl.add_column("#", style="dim")
    tbl.add_column("Time", style="dim")
    tbl.add_column("Decision")
    tbl.add_column("Conf", justify="right")
    tbl.add_column("ms", justify="right", style="dim")
    tbl.add_column("Status")

    for d in decisions:
        status_style = "green" if d.get("status") == "completed" else "red"
        tbl.add_row(
            str(d.get("id", "")),
            d.get("timestamp", "")[:19],
            str(d.get("decision", ""))[:50],
            f"{d.get('confidence', 0):.2f}",
            str(d.get("latency_ms", "")),
            f"[{status_style}]{d.get('status', '')}[/]",
        )

    console.print()
    console.print(tbl)
    console.print()


def _scan(symbols_str: str):
    """Publish a market scan request to NATS."""
    import json
    import nats as nats_lib
    from datetime import datetime, timezone

    symbols = symbols_str.upper().split()
    if not symbols:
        console.print("  [yellow]Usage: scan SPY QQQ BTC-USD[/]")
        return

    async def _publish():
        nc = await nats_lib.connect(os.getenv("NATS_URL", "nats://localhost:4222"))
        payload = json.dumps({
            "request_id": f"scan-{datetime.now(timezone.utc).strftime('%H%M%S')}",
            "request_type": "market_scan",
            "symbols": symbols,
            "timeframe": "1d",
        })
        await nc.publish("sentinel.market.data", payload.encode())
        await nc.flush()
        await nc.close()

    try:
        asyncio.run(_publish())
        console.print(f"  [green]📡 Scan published →[/] sentinel.market.data: {', '.join(symbols)}")
        console.print(f"  [dim]MarketAgent will process in background.[/]\n")
    except Exception as e:
        console.print(f"  [red]Failed to publish: {e}[/]\n")


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    global swarm_instance, team_instance
    current_mode = "solo"

    console.clear()
    console.print(BANNER)

    # First-run setup — if no .env or no LLM key, run interactive setup
    if not os.path.exists(".env") or not _has_llm_key():
        first_run_setup()

    # Re-check after setup — if user still has no key, exit
    if not _has_llm_key() and os.getenv("LLM_PROVIDER", "CLAUDE") != "OLLAMA":
        console.print("  [yellow]⚠ LLM_API_KEY not set. Run again to configure.[/]\n")
        return

    # Bridge LLM_API_KEY → provider-specific env vars for Upsonic/Agno
    _bridge_api_keys()

    # Validate model config — catch misconfigs early
    if not _validate_model_config():
        return

    # Start NATS subscriber in background
    try:
        _start_nats_subscriber()
        import time
        time.sleep(1)
    except Exception as e:
        console.print(f"  [yellow]⚠ NATS connection failed: {e}[/]")
        console.print(f"  [dim]Run 'docker compose up -d nats' first.[/]\n")

    # Start REST API server in background
    try:
        _start_api_server()
    except Exception as e:
        console.print(f"  [yellow]⚠ REST API failed: {e}[/]")

    # Show status
    _print_status(
        nats_connected=nats_status["connected"],
        decisions_logged=nats_status["decisions"],
        mode=current_mode,
    )

    console.print()
    if nats_status["connected"]:
        console.print("  [green]Ready![/] MarketAgent listening on NATS.")
    console.print("  [dim]Type a question, 'swarm'/'team'/'solo' to switch, or 'help' for commands.[/]\n")

    # Interactive loop
    while True:
        try:
            prompt = "[bold magenta]  ⚡ Swarm →[/] " if current_mode == "swarm" else "[bold cyan]  ⚡ You →[/] "
            user_input = console.input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n\n  [bold]Goodbye![/]\n")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("quit", "exit", "q"):
            console.print("\n  [bold]Goodbye![/]\n")
            break

        if cmd == "clear":
            console.clear()
            console.print(BANNER)
            _print_status(nats_status["connected"], nats_status["decisions"], current_mode)
            console.print()
            continue

        # ── Browser commands: Tier 1 (open X) vs Tier 2 (browse <task>) ──
        # Tier 1: "open youtube", "go to tradingview" → instant Chrome open
        if cmd.startswith(("open ", "go to ", "launch ", "navigate to ")):
            from automation.browser import is_browser_command, open_in_browser
            if is_browser_command(user_input):
                console.print(f"\n  [cyan]🌐 Opening in Chrome...[/]")
                result = open_in_browser(user_input)
                console.print(f"  {result}\n")
                continue

        # Tier 2: "browse <complex task>" → LLM-driven browser automation
        if cmd.startswith("browse "):
            task = user_input[7:].strip()
            if not task:
                console.print("  [yellow]Usage: browse <task>[/]")
                console.print("  [dim]Examples:[/]")
                console.print("    [cyan]browse check BTC price on tradingview[/]")
                console.print("    [cyan]browse find trending tokens on coingecko[/]")
                console.print("    [cyan]browse screenshot dexscreener.com/solana[/]\n")
                continue
            console.print(f"\n  [cyan]🤖 Browser agent working on: {task}[/]")
            console.print(f"  [dim]Using Tier 2 (LLM + Playwright) — this may take a moment...[/]")
            try:
                from automation.browser import get_browser_agent
                agent = get_browser_agent(prefer_computer_use=False)
                result = agent.browse_sync(task)
                console.print(f"\n  [bold cyan]🌐 Browser →[/] {result}\n")
            except Exception as e:
                console.print(f"\n  [red]Browser error: {e}[/]")
                console.print(f"  [dim]Make sure browser-use is installed: uv add browser-use langchain-anthropic[/]\n")
            continue

        # ── Add commands: add <service> → interactive API key setup ──
        if cmd.startswith("add"):
            parts = cmd.split(maxsplit=1)
            service = parts[1] if len(parts) > 1 else ""
            _handle_add(service)
            continue

        if cmd == "status":
            _print_status(nats_status["connected"], nats_status["decisions"], current_mode)
            continue

        if cmd in ("help", "?", "commands"):
            _print_help(current_mode)
            continue

        if cmd == "swarm":
            console.print()
            console.print("  [bold magenta]🐝 Activating Agno swarm...[/]")
            try:
                from agents.swarm import SwarmAgent
                with console.status("[magenta]Initializing 5-agent Agno team...[/]"):
                    swarm_instance = SwarmAgent()
                current_mode = "swarm"
                console.print("  [green]✓ Swarm active![/] Captain + Analyst + Trader + Risk Mgr + Ops")
                _print_status(nats_status["connected"], nats_status["decisions"], current_mode)
            except Exception as e:
                console.print(f"  [red]Failed to initialize swarm: {e}[/]")
                console.print(f"  [dim]Make sure agno is installed: uv add agno[/]")
            console.print()
            continue

        if cmd == "team":
            console.print()
            console.print("  [bold green]🧠 Activating Upsonic Team...[/]")
            try:
                from agents.team import build_team
                with console.status("[green]Building Upsonic Team (coordinate mode)...[/]"):
                    team_instance = build_team()
                current_mode = "team"
                console.print("  [green]✓ Team active![/] Analyst + RiskManager + Trader (Upsonic coordinate)")
                _print_status(nats_status["connected"], nats_status["decisions"], current_mode)
            except Exception as e:
                console.print(f"  [red]Failed to initialize team: {e}[/]")
            console.print()
            continue

        if cmd == "solo":
            current_mode = "solo"
            swarm_instance = None
            team_instance = None
            console.print("\n  [cyan]Switched to solo mode (MarketAgent).[/]\n")
            continue

        if cmd == "sentinel":
            _start_sentinel()
            continue

        if cmd == "sentinel stop":
            _stop_sentinel()
            continue

        if cmd == "guardrails":
            _show_guardrails()
            continue

        if cmd.startswith("mission"):
            _handle_mission(cmd.split())
            continue

        if cmd.startswith("logs"):
            parts = cmd.split()
            n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
            _show_logs(n)
            continue

        if cmd.startswith("scan "):
            _scan(user_input[5:])
            continue

        # Everything else → chat with active agent
        if current_mode == "swarm":
            _chat_swarm(user_input)
        elif current_mode == "team":
            _chat_team(user_input)
        else:
            _chat_solo(user_input)


if __name__ == "__main__":
    main()
