"""
Sentinel v2 — Autonomous Crypto Surveillance & Execution Runtime

Core autonomous loop that runs 24/7:

1. Tier-1: Raw API data → threshold checks (no LLM cost)
2. Tier-2: On alert → route to Upsonic Team specialists for analysis
3. Missions: Standing orders that execute on schedule
4. Memory: Upsonic Memory (SQLite) + v1 MemoryStore for snapshots
5. Notifications: Telegram + console logs
6. NATS: Publishes all alerts to sentinel.alert.* subjects

Usage:
    uv run sentinel.py              # Run autonomous loop
    uv run sentinel.py --once       # Run all monitors once and exit
    uv run main.py → 'sentinel'    # Start from interactive mode
"""

import os
import sys
import json
import time
import signal
import logging
import asyncio
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("sentinel.log", mode="a"),
    ],
)
# Suppress noisy httpx logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("sentinel")
console = Console()


# ── Guardrails ───────────────────────────────────────────────────────

_active_guardrails = None  # Set during Sentinel.__init__()


class Guardrails:
    """Hard limits on autonomous execution."""

    def __init__(self):
        self.max_trade_usd = float(os.getenv("SENTINEL_MAX_TRADE_USD", "100"))
        self.max_daily_trades = int(os.getenv("SENTINEL_MAX_DAILY_TRADES", "5"))
        self.max_daily_loss_usd = float(os.getenv("SENTINEL_MAX_DAILY_LOSS", "250"))
        self.auto_execute_enabled = os.getenv("SENTINEL_AUTO_EXECUTE", "false").lower() == "true"
        self.kill_switch = False

        self._trades_today = 0
        self._daily_pnl = 0.0
        self._trade_date = datetime.now().date()

    def can_execute(self, trade_usd: float = 0) -> tuple[bool, str]:
        """Check if an autonomous trade is allowed."""
        if self.kill_switch:
            return False, "🛑 Kill switch active — all trading halted"

        if not self.auto_execute_enabled:
            return False, "Auto-execute disabled — requires manual approval"

        # Reset daily counters
        today = datetime.now().date()
        if today != self._trade_date:
            self._trades_today = 0
            self._daily_pnl = 0.0
            self._trade_date = today

        if self._trades_today >= self.max_daily_trades:
            return False, f"Daily trade limit reached ({self.max_daily_trades})"

        if trade_usd > self.max_trade_usd:
            return False, f"Trade ${trade_usd:.2f} exceeds max ${self.max_trade_usd:.2f}"

        if abs(self._daily_pnl) >= self.max_daily_loss_usd:
            return False, f"Daily loss limit reached (${self.max_daily_loss_usd:.2f})"

        return True, "✅ Within guardrail limits"

    def record_trade(self, pnl: float = 0):
        self._trades_today += 1
        self._daily_pnl += pnl

    def engage_kill_switch(self):
        self.kill_switch = True
        logger.critical("🛑 KILL SWITCH ENGAGED — All autonomous trading halted")

    def status(self) -> dict:
        return {
            "auto_execute": self.auto_execute_enabled,
            "kill_switch": self.kill_switch,
            "trades_today": f"{self._trades_today}/{self.max_daily_trades}",
            "daily_pnl": f"${self._daily_pnl:+.2f}",
            "max_trade": f"${self.max_trade_usd:.2f}",
            "max_daily_loss": f"${self.max_daily_loss_usd:.2f}",
        }


# ── Notifier ─────────────────────────────────────────────────────────

class Notifier:
    """Sends alerts to Telegram bot and/or logs."""

    def __init__(self):
        self._bot = None
        self._chat_id = None
        self._setup_telegram()

    def _setup_telegram(self):
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if token:
            try:
                from telegram import Bot
                self._bot = Bot(token=token)
                self._chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
                logger.info("Telegram notifier ready")
            except Exception as e:
                logger.warning(f"Telegram setup failed: {e}")

    def send_sync(self, message: str, channel: str = "alerts"):
        """Send a notification synchronously."""
        logger.info(f"[{channel}] {message[:200]}")

        if self._bot and self._chat_id:
            try:
                async def _send():
                    await self._bot.send_message(
                        chat_id=int(self._chat_id),
                        text=f"🛡️ [{channel.upper()}]\n\n{message[:4000]}",
                    )
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(_send())
                    else:
                        loop.run_until_complete(_send())
                except RuntimeError:
                    asyncio.run(_send())
            except Exception as e:
                logger.error(f"Telegram send failed: {e}")


# ── NATS Publisher ───────────────────────────────────────────────────

class NATSPublisher:
    """Publishes alerts and events to NATS subjects."""

    def __init__(self):
        self._nc = None
        self._connected = False

    async def connect(self):
        """Connect to NATS server."""
        try:
            import nats as nats_lib
            self._nc = await nats_lib.connect(
                os.getenv("NATS_URL", "nats://localhost:4222"),
                name="sentinel-autonomous",
                max_reconnect_attempts=5,
                reconnect_time_wait=2,
            )
            self._connected = True
            logger.info("NATS publisher connected")
        except Exception as e:
            logger.warning(f"NATS publisher failed: {e}")
            self._connected = False

    def publish_sync(self, subject: str, data: dict):
        """Publish a message to NATS synchronously."""
        if not self._connected or not self._nc:
            return
        try:
            payload = json.dumps(data).encode()

            async def _pub():
                await self._nc.publish(subject, payload)
                await self._nc.flush()

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_pub())
                else:
                    loop.run_until_complete(_pub())
            except RuntimeError:
                asyncio.run(_pub())
        except Exception as e:
            logger.error(f"NATS publish failed: {e}")


# ── Upsonic Team Builder ────────────────────────────────────────────

def _build_upsonic_team():
    """Build the Upsonic Team for Tier-2 analysis."""
    try:
        from upsonic import Agent, Task, Team

        # Detect model
        provider = os.getenv("LLM_PROVIDER", "CLAUDE").upper()
        model_map = {
            "CLAUDE": "anthropic/claude-sonnet-4-5",
            "GEMINI": f"google/{os.getenv('LLM_MODEL', 'gemini-2.0-flash')}",
            "GROK": f"xai/{os.getenv('LLM_MODEL', 'grok-2')}",
        }
        model = model_map.get(provider, "anthropic/claude-sonnet-4-5")

        # Bridge API key to provider-specific env var
        api_key = os.getenv("LLM_API_KEY", "")
        if provider == "CLAUDE" and api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
        elif provider == "GEMINI" and api_key:
            os.environ["GEMINI_API_KEY"] = api_key

        # Memory
        memory = None
        try:
            from upsonic.storage.memory.memory import Memory
            from upsonic.storage.providers.sqlite import SqliteStorage
            storage = SqliteStorage("sessions", "profiles", "sentinel_memory.db")
            memory = Memory(
                storage=storage,
                session_id="sentinel_autonomous",
                user_id="sentinel",
                full_session_memory=True,
                summary_memory=True,
            )
            logger.info("Upsonic SQLite memory ready")
        except Exception as e:
            logger.warning(f"Upsonic memory unavailable: {e}")

        # Analyst Agent
        analyst = Agent(
            name="Analyst",
            model=model,
            role="Market Research & Macro Analysis Specialist",
            goal="Research markets, analyze macro, surface sentiment signals",
            instructions=(
                "Use CoinGecko for crypto prices. FRED for macro (GDP, CPI, rates, VIX). "
                "Y2 for news sentiment. Elfa for social trending. Be quantitative. "
                "Cite specific numbers, changes, percentages. Flag anything unusual."
            ),
            memory=memory,
            retry=2,
        )

        # Risk Manager Agent
        risk_mgr = Agent(
            name="RiskManager",
            model=model,
            role="Portfolio Risk & Position Sizing Specialist",
            goal="Assess risk, size positions, protect capital",
            instructions=(
                "Max 5% equity per trade. Flag if leverage >3x. Warn if one asset >30% of portfolio. "
                "Consider macro conditions for risk adjustments. You APPROVE or REJECT trade proposals."
            ),
            memory=memory,
            retry=2,
        )

        # Trader Agent
        trader = Agent(
            name="Trader",
            model=model,
            role="Trade Execution Specialist",
            goal="Execute trades precisely across Hyperliquid, Aster, Polymarket",
            instructions=(
                "ALWAYS confirm before executing trades. State exact order: venue, direction, size, price. "
                "After execution, report fill price and order ID. For market data, act freely."
            ),
            memory=memory,
            retry=2,
        )

        # Team (coordinate mode — leader agent decides who to delegate to)
        team = Team(
            agents=[analyst, risk_mgr, trader],
            mode="coordinate",
            model=model,
            memory=memory,
        )

        return team, analyst, risk_mgr, trader
    except Exception as e:
        logger.error(f"Upsonic Team build failed: {e}")
        return None, None, None, None


# ── Chat Function Wrapper ────────────────────────────────────────────

def _agent_chat(team, message: str) -> str:
    """Send a message to the Upsonic Team and get a response."""
    if team is None:
        return "Team not initialized."
    try:
        from upsonic import Task
        from tools import ALL_TOOLS
        task = Task(description=message, tools=ALL_TOOLS)
        result = team.do([task])
        return str(result) if result else "No response."
    except Exception as e:
        logger.error(f"Team chat failed: {e}")
        return f"Error: {e}"


# ── Sentinel Core ────────────────────────────────────────────────────

class Sentinel:
    """The autonomous runtime — monitors, decides, acts, notifies."""

    def __init__(self):
        self.guardrails = Guardrails()
        self.notifier = Notifier()
        self.nats_pub = NATSPublisher()

        # Expose guardrails globally
        import sentinel as _sentinel_module
        _sentinel_module._active_guardrails = self.guardrails

        # Core components (loaded in initialize)
        self.team = None
        self.analyst = None
        self.risk_mgr = None
        self.trader = None
        self.memory = None
        self.missions = None
        self.scheduler = None

        # Monitors
        self.price_monitor = None
        self.position_monitor = None
        self.sentiment_monitor = None
        self.macro_monitor = None

    def initialize(self) -> bool:
        """Boot up all systems."""
        console.print(Panel(
            "[bold]🛡️ SENTINEL v2 — Autonomous Mode[/]\n"
            "[dim]Monitors · Upsonic Team · Missions · Guardrails · NATS[/]",
            border_style="bold cyan",
        ))

        # ── 1. Upsonic Team ──
        console.print("  Loading Upsonic Team...", end=" ")
        self.team, self.analyst, self.risk_mgr, self.trader = _build_upsonic_team()
        if self.team:
            console.print("[green]✓[/] (Analyst + RiskManager + Trader)")
        else:
            console.print("[red]✗ Failed to build team[/]")
            return False

        # Chat function for monitors (wraps team.do)
        def team_chat(msg):
            return _agent_chat(self.team, msg)

        # ── 2. NATS Publisher ──
        console.print("  Connecting NATS publisher...", end=" ")
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.nats_pub.connect())
            if self.nats_pub._connected:
                console.print("[green]✓[/]")
            else:
                console.print("[yellow]○ offline[/]")
        except Exception:
            console.print("[yellow]○ offline[/]")

        # ── 3. Memory Store ──
        console.print("  Loading memory...", end=" ")
        try:
            from memory import MemoryStore
            self.memory = MemoryStore()
            stats = self.memory.get_stats()
            console.print(f"[green]✓[/] ({stats['backend']})")
        except Exception as e:
            console.print(f"[yellow]✗ {e}[/]")
            self.memory = None

        # ── 4. Mission Controller ──
        console.print("  Loading missions...", end=" ")
        try:
            from missions import MissionController
            self.missions = MissionController()
            active = self.missions.get_active_missions()
            console.print(f"[green]✓[/] ({len(active)} active)")
        except Exception as e:
            console.print(f"[yellow]✗ {e}[/]")
            self.missions = None

        # ── 5. Monitors (two-tier) ──
        from monitors import PriceMonitor, PositionMonitor, SentimentMonitor, MacroMonitor

        self.price_monitor = PriceMonitor(agent_chat_fn=team_chat)
        self.position_monitor = PositionMonitor(agent_chat_fn=team_chat)
        self.sentiment_monitor = SentimentMonitor(agent_chat_fn=team_chat)
        self.macro_monitor = MacroMonitor(agent_chat_fn=team_chat)

        # Configurable watchlist
        watchlist_raw = os.getenv("SENTINEL_WATCHLIST", "bitcoin:5.0,ethereum:7.0")
        for entry in watchlist_raw.split(","):
            entry = entry.strip()
            if ":" in entry:
                sym, pct = entry.split(":", 1)
                self.price_monitor.add_watch(sym.strip(), change_pct=float(pct.strip()))
            elif entry:
                self.price_monitor.add_watch(entry.strip(), change_pct=5.0)

        monitors_loaded = ["price", "position", "sentiment"]
        if self.macro_monitor.fred_key:
            monitors_loaded.append("macro")
        console.print(f"  Monitors: [green]{', '.join(monitors_loaded)}[/]")

        # ── 6. Scheduler ──
        from scheduler import SentinelScheduler
        self.scheduler = SentinelScheduler()

        self.scheduler.every(15, self.run_price_check, "price_check")
        self.scheduler.every(30, self.run_position_check, "position_check")
        self.scheduler.every(60, self.run_sentiment_check, "sentiment_check")

        if self.macro_monitor.fred_key:
            self.scheduler.every(360, self.run_macro_check, "macro_check")

        self.scheduler.every(60, self.run_snapshot, "portfolio_snapshot")

        if self.missions:
            self.scheduler.every(5, self.run_missions, "mission_runner")

        console.print("  Scheduler: [green]price/15m · positions/30m · sentiment/60m · snapshots/60m · missions/5m[/]")

        # ── 7. Strategy Runner ──
        try:
            from strategy_runner import StrategyRunner
            self.strategy_runner = StrategyRunner(
                guardrails=self.guardrails,
                notifier=self.notifier,
            )
            if self.strategy_runner.enabled:
                self.scheduler.every(5, self.strategy_runner.run, "sma_strategy")
                console.print(
                    f"  Strategy: [green]SMA({self.strategy_runner.fast_sma}/{self.strategy_runner.slow_sma}) "
                    f"on {self.strategy_runner.symbol} every 5m (~${self.strategy_runner.trade_usd}/trade)[/]"
                )
            else:
                console.print("  Strategy: [dim]disabled (STRATEGY_ENABLED=false)[/]")
        except Exception as e:
            self.strategy_runner = None
            console.print(f"  Strategy: [dim]unavailable ({e})[/]")

        self._print_status()
        return True

    def _print_status(self):
        """Print sentinel status dashboard."""
        console.print()
        g = self.guardrails.status()

        status = Table(show_header=False, box=None, padding=(0, 2))
        status.add_column("Key", style="bold")
        status.add_column("Value")

        status.add_row("Auto-Execute", "[green]ON[/]" if g["auto_execute"] else "[yellow]OFF[/]")
        status.add_row("Kill Switch", "[red]ENGAGED[/]" if g["kill_switch"] else "[green]OK[/]")
        status.add_row("Trades Today", g["trades_today"])
        status.add_row("Daily PnL", g["daily_pnl"])
        status.add_row("Max Trade / Max Loss", f"{g['max_trade']} / {g['max_daily_loss']}")
        status.add_row("Framework", "Upsonic Team (coordinate)")
        status.add_row("Memory", self.memory.get_stats()["backend"] if self.memory else "none")
        status.add_row("Active Missions", str(len(self.missions.get_active_missions())) if self.missions else "0")

        console.print(Panel(status, title="🛡️ Sentinel Dashboard", border_style="cyan"))

    # ── Monitor Runners (Tier 1: raw data, Tier 2: LLM on alert) ─────

    def run_price_check(self):
        """Tier-1 price check — direct CoinGecko API, no LLM."""
        alerts = self.price_monitor.check()
        for alert in alerts:
            self._handle_alert(alert)

    def run_position_check(self):
        """Position check — triggers LLM only if agent is needed."""
        alerts = self.position_monitor.check()
        for alert in alerts:
            self._handle_alert(alert)

    def run_sentiment_check(self):
        """Sentiment check."""
        alerts = self.sentiment_monitor.check()
        for alert in alerts:
            self._handle_alert(alert)

    def run_macro_check(self):
        """Tier-1 FRED macro data check — no LLM."""
        if self.macro_monitor:
            alerts = self.macro_monitor.check()
            for alert in alerts:
                self._handle_alert(alert)

    def run_snapshot(self):
        """Take a portfolio snapshot for equity curve tracking — direct API, no LLM."""
        if not self.memory:
            return
        try:
            import requests as req
            total_equity = 0.0
            all_positions = []

            # Hyperliquid
            wallet = os.getenv("HYPERLIQUID_WALLET_ADDRESS", "").strip()
            if wallet:
                try:
                    resp = req.post(
                        "https://api.hyperliquid.xyz/info",
                        json={"type": "clearinghouseState", "user": wallet},
                        timeout=10,
                    )
                    resp.raise_for_status()
                    state = resp.json()
                    hl_equity = float(state.get("marginSummary", {}).get("accountValue", 0))
                    total_equity += hl_equity
                    for pos_w in state.get("assetPositions", []):
                        pos = pos_w.get("position", {})
                        size = float(pos.get("szi", 0))
                        if size != 0:
                            all_positions.append({
                                "venue": "hyperliquid",
                                "symbol": pos.get("coin", ""),
                                "size": size,
                                "entry_price": float(pos.get("entryPx", 0)),
                                "unrealized_pnl": float(pos.get("unrealizedPnl", 0)),
                            })
                except Exception as e:
                    logger.warning(f"Snapshot: HL fetch failed: {e}")

            # Aster
            try:
                from scrapers.aster_scraper import aster_balance, aster_positions
                bal = aster_balance()
                if isinstance(bal, dict) and not bal.get("error"):
                    total_equity += float(bal.get("totalWalletBalance", 0))
                positions = aster_positions()
                if isinstance(positions, list):
                    for pos in positions:
                        size = float(pos.get("positionAmt", 0))
                        if size != 0:
                            all_positions.append({
                                "venue": "aster",
                                "symbol": pos.get("symbol", ""),
                                "size": size,
                                "entry_price": float(pos.get("entryPrice", 0)),
                                "unrealized_pnl": float(pos.get("unRealizedProfit", 0)),
                            })
            except Exception as e:
                logger.warning(f"Snapshot: Aster fetch failed: {e}")

            self.memory.save_snapshot(
                total_equity=total_equity,
                positions=all_positions,
            )
        except Exception as e:
            logger.error(f"Snapshot failed: {e}")

    def run_missions(self):
        """Execute any active missions that are due."""
        if not self.missions:
            return

        for mission in self.missions.get_active_missions():
            if mission.last_run:
                from datetime import datetime as dt
                last = dt.fromisoformat(mission.last_run)
                elapsed = (dt.now() - last).total_seconds() / 60
                if elapsed < mission.interval_minutes:
                    continue

            try:
                chat_fn = lambda msg: _agent_chat(self.team, msg)
                result = self.missions.execute_mission(mission, chat_fn)

                if self.memory:
                    self.memory.log_decision(
                        monitor="mission",
                        alert_title=mission.name,
                        action="mission_executed",
                        result=result[:500],
                        data={"mission_id": mission.id, "template": mission.template},
                    )
                self.notifier.send_sync(f"📋 {mission.name}\n\n{result[:500]}", channel="missions")
            except Exception as e:
                logger.error(f"Mission {mission.name} failed: {e}")

    # ── Alert Handler ────────────────────────────────────────────────

    def _handle_alert(self, alert):
        """Process alert: log → NATS publish → notify → route to specialist."""
        logger.info(f"Alert: {alert.title}")

        # 1. Publish to NATS
        self.nats_pub.publish_sync(f"sentinel.alert.{alert.monitor}", alert.to_dict())

        # 2. Log to memory
        if self.memory:
            self.memory.log_decision(
                monitor=alert.monitor,
                alert_title=alert.title,
                action="alert_received",
                result=alert.message,
                data=alert.data,
            )

        # 3. Always notify
        self.notifier.send_sync(f"{alert.title}\n{alert.message}", channel="alerts")

        # 4. Auto-execute if enabled + guardrails pass
        if alert.auto_execute:
            can_exec, reason = self.guardrails.can_execute()
            if can_exec:
                response = _agent_chat(
                    self.team,
                    f"AUTONOMOUS ACTION REQUIRED:\n"
                    f"Alert: {alert.title}\n"
                    f"Details: {alert.message}\n"
                    f"Data: {json.dumps(alert.data)}\n\n"
                    f"Decide and execute the appropriate action. "
                    f"Keep position sizes under ${self.guardrails.max_trade_usd}.",
                )

                if self.memory:
                    self.memory.log_decision(
                        monitor=alert.monitor,
                        alert_title=alert.title,
                        action="auto_execute",
                        result=response[:500],
                        auto_executed=True,
                        data=alert.data,
                    )
                self.guardrails.record_trade()
                self.notifier.send_sync(f"🤖 Auto-executed:\n{response[:500]}", channel="trades")
                self.nats_pub.publish_sync("sentinel.trade.auto", {
                    "alert": alert.title, "response": response[:500],
                })
            else:
                self.notifier.send_sync(f"⚠️ Blocked: {reason}\n\nAlert: {alert.title}", channel="alerts")
        else:
            if self.memory:
                self.memory.log_decision(
                    monitor=alert.monitor, alert_title=alert.title,
                    action="notify_only", result=alert.message, data=alert.data,
                )

    # ── Main Loop ────────────────────────────────────────────────────

    def run(self, once: bool = False):
        """Start the autonomous loop."""
        if not self.initialize():
            console.print("[red]  Failed to initialize. Exiting.[/]")
            return

        if once:
            console.print("\n  [cyan]Running all monitors once...[/]\n")
            self.run_price_check()
            self.run_position_check()
            self.run_sentiment_check()
            self.run_snapshot()
            self.run_missions()
            console.print("\n  [green]Done.[/]")
            return

        # Start scheduler
        self.scheduler.start()

        console.print(f"\n  [bold green]🛡️ Sentinel v2 is live — monitoring 24/7[/]")
        console.print(f"  [dim]Press Ctrl+C to stop[/]\n")

        # Graceful shutdown
        def shutdown(sig, frame):
            console.print("\n  [yellow]Shutting down Sentinel...[/]")
            self.scheduler.stop()
            if self.memory:
                self.memory.remember("last_shutdown", datetime.now().isoformat())
            console.print("  [green]Sentinel stopped.[/]")
            sys.exit(0)

        try:
            signal.signal(signal.SIGINT, shutdown)
            signal.signal(signal.SIGTERM, shutdown)
        except ValueError:
            # signal.signal() only works in main thread — when running from
            # main.py's REPL thread, the main thread handles Ctrl+C instead
            pass

        while True:
            time.sleep(1)


# ── Entry Point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    sentinel = Sentinel()
    once = "--once" in sys.argv
    sentinel.run(once=once)
