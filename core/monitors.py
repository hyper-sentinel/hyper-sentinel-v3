"""
Sentinel Monitors — Two-tier monitoring with direct API data.

Tier 1: Raw data fetch via APIs → threshold comparison (no LLM cost)
Tier 2: When alert fires → engage agent specialist for analysis

Monitors:
  • PriceMonitor    — CoinGecko direct API → threshold alerts
  • PositionMonitor — Hyperliquid SDK direct → drawdown/leverage alerts
  • SentimentMonitor — Elfa/Y2 via agent → baseline delta detection
  • MacroMonitor    — FRED direct API → regime change detection
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("sentinel.monitors")


class Alert:
    """Represents a detected event that needs action."""

    def __init__(
        self,
        monitor: str,
        severity: str,  # "info", "warning", "critical"
        title: str,
        message: str,
        data: dict | None = None,
        auto_execute: bool = False,
    ):
        self.monitor = monitor
        self.severity = severity
        self.title = title
        self.message = message
        self.data = data or {}
        self.auto_execute = auto_execute
        self.timestamp = datetime.now().isoformat()

    def __repr__(self):
        return f"Alert({self.severity}: {self.title})"

    def to_dict(self) -> dict:
        return {
            "monitor": self.monitor,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "auto_execute": self.auto_execute,
            "timestamp": self.timestamp,
        }


# ── Price Monitor (Tier 1 — no LLM) ─────────────────────────────────

class PriceMonitor:
    """
    Tier-1: Direct CoinGecko API calls, zero LLM cost.
    Only triggers agent when thresholds are breached.
    """

    def __init__(self, agent_chat_fn=None):
        self.agent_chat = agent_chat_fn
        self.watchlist: list[dict] = []
        self._last_prices: dict[str, float] = {}

    def add_watch(
        self,
        symbol: str,
        above: float | None = None,
        below: float | None = None,
        change_pct: float | None = None,
    ):
        self.watchlist.append({
            "symbol": symbol.lower(),
            "above": above,
            "below": below,
            "change_pct": change_pct,
            "triggered": False,
        })
        logger.info(f"Watching {symbol}: above={above}, below={below}, change={change_pct}%")

    def check(self) -> list[Alert]:
        """Tier-1: Direct API, no LLM calls."""
        alerts = []

        try:
            import requests

            symbols = list(set(w["symbol"] for w in self.watchlist))
            if not symbols:
                return alerts

            resp = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": ",".join(symbols),
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            for watch in self.watchlist:
                sym = watch["symbol"]
                if sym not in data:
                    continue

                price = data[sym].get("usd", 0)
                change_24h = data[sym].get("usd_24h_change", 0) or 0
                self._last_prices[sym] = price

                if watch["above"] and price >= watch["above"] and not watch["triggered"]:
                    watch["triggered"] = True
                    alerts.append(Alert(
                        monitor="price",
                        severity="warning",
                        title=f"🔺 {sym.upper()} above ${watch['above']:,.2f}",
                        message=f"{sym.upper()} at ${price:,.2f} (24h: {change_24h:+.1f}%)",
                        data={"symbol": sym, "price": price, "change_24h": change_24h},
                    ))

                if watch["below"] and price <= watch["below"] and not watch["triggered"]:
                    watch["triggered"] = True
                    alerts.append(Alert(
                        monitor="price",
                        severity="critical",
                        title=f"🔻 {sym.upper()} below ${watch['below']:,.2f}",
                        message=f"{sym.upper()} at ${price:,.2f} (24h: {change_24h:+.1f}%)",
                        data={"symbol": sym, "price": price, "change_24h": change_24h},
                    ))

                if watch["change_pct"] and abs(change_24h) >= watch["change_pct"]:
                    direction = "📈" if change_24h > 0 else "📉"
                    alerts.append(Alert(
                        monitor="price",
                        severity="warning",
                        title=f"{direction} {sym.upper()} moved {change_24h:+.1f}% in 24h",
                        message=f"{sym.upper()} at ${price:,.2f}",
                        data={"symbol": sym, "price": price, "change_24h": change_24h},
                    ))

        except Exception as e:
            logger.error(f"Price monitor error: {e}")
            alerts.append(Alert(
                monitor="price",
                severity="error",
                title="Price Monitor Failed",
                message=f"Monitor check failed: {str(e)[:200]}",
                data={"error": str(e), "error_type": type(e).__name__},
                auto_execute=False,
            ))

        return alerts


# ── Position Monitor (Tier 1 — Direct SDK) ───────────────────────────

class PositionMonitor:
    """
    Tier-1: Direct Hyperliquid SDK for structured position data.
    Only uses LLM when risk thresholds are breached.
    """

    def __init__(self, agent_chat_fn=None):
        self.agent_chat = agent_chat_fn
        self.max_drawdown_pct: float = float(os.getenv("SENTINEL_MAX_DRAWDOWN_PCT", "5.0"))
        self.max_leverage: float = float(os.getenv("SENTINEL_MAX_LEVERAGE", "10.0"))

    def check(self) -> list[Alert]:
        """Tier-1: Try direct SDK, fall back to agent."""
        alerts = []

        # Try direct Hyperliquid SDK first (no LLM cost)
        try:
            wallet = os.getenv("HYPERLIQUID_WALLET_ADDRESS", "").strip()
            if wallet:
                return self._check_direct(wallet)
        except Exception as e:
            logger.debug(f"Direct SDK failed, falling back to agent: {e}")

        # Fallback: use agent (costs LLM call)
        return self._check_via_agent()

    def _check_direct(self, wallet: str) -> list[Alert]:
        """Direct Hyperliquid API — structured data, no LLM."""
        alerts = []
        try:
            import requests

            # Hyperliquid info API
            resp = requests.post(
                "https://api.hyperliquid.xyz/info",
                json={"type": "clearinghouseState", "user": wallet},
                timeout=10,
            )
            resp.raise_for_status()
            state = resp.json()

            positions = state.get("assetPositions", [])
            for pos_wrapper in positions:
                pos = pos_wrapper.get("position", {})
                symbol = pos.get("coin", "?")
                size = float(pos.get("szi", 0))
                entry_px = float(pos.get("entryPx", 0))
                mark_px = float(pos.get("positionValue", 0)) / abs(size) if size else 0
                leverage = float(pos.get("leverage", {}).get("value", 0))
                unrealized_pnl = float(pos.get("unrealizedPnl", 0))

                if abs(size) == 0:
                    continue

                # Calculate PnL percentage
                pnl_pct = (unrealized_pnl / (abs(size) * entry_px) * 100) if entry_px else 0

                # Check drawdown
                if pnl_pct < -self.max_drawdown_pct:
                    alerts.append(Alert(
                        monitor="position",
                        severity="critical",
                        title=f"⚠️ {symbol} down {pnl_pct:.1f}%",
                        message=(
                            f"{symbol}: PnL {pnl_pct:+.1f}% (${unrealized_pnl:+,.2f})\n"
                            f"Size: {size}, Entry: ${entry_px:,.2f}, Leverage: {leverage}x"
                        ),
                        data={
                            "symbol": symbol, "size": size, "entry_px": entry_px,
                            "pnl_pct": pnl_pct, "pnl_usd": unrealized_pnl,
                            "leverage": leverage,
                        },
                        auto_execute=False,
                    ))

                # Check leverage
                if leverage > self.max_leverage:
                    alerts.append(Alert(
                        monitor="position",
                        severity="warning",
                        title=f"⚠️ {symbol} leverage {leverage}x exceeds {self.max_leverage}x",
                        message=f"{symbol}: {leverage}x leverage, PnL {pnl_pct:+.1f}%",
                        data={"symbol": symbol, "leverage": leverage, "max": self.max_leverage},
                    ))

            logger.info(f"Position check: {len(positions)} positions, {len(alerts)} alerts")

        except Exception as e:
            logger.error(f"Direct position check failed: {e}")
            alerts.append(Alert(
                monitor="position",
                severity="error",
                title="Position Monitor Failed",
                message=f"Monitor check failed: {str(e)[:200]}",
                data={"error": str(e), "error_type": type(e).__name__},
                auto_execute=False,
            ))

        # ── Aster DEX positions (Task 8) ──
        try:
            from scrapers.aster_scraper import aster_positions
            aster_pos = aster_positions()
            if isinstance(aster_pos, list):
                for pos in aster_pos:
                    size = float(pos.get("positionAmt", 0))
                    if size == 0:
                        continue
                    entry = float(pos.get("entryPrice", 0))
                    mark = float(pos.get("markPrice", 0))
                    upnl = float(pos.get("unRealizedProfit", 0))
                    leverage = float(pos.get("leverage", 0))
                    liq_price = float(pos.get("liquidationPrice", 0))
                    symbol = pos.get("symbol", "?")

                    # PnL % check
                    if entry > 0:
                        pnl_pct = (upnl / (abs(size) * entry)) * 100
                        if pnl_pct < -self.max_drawdown_pct:
                            alerts.append(Alert(
                                monitor="position",
                                severity="critical",
                                title=f"Aster {symbol}: {pnl_pct:+.1f}% drawdown",
                                message=f"Entry: ${entry:,.2f} | Mark: ${mark:,.2f} | PnL: ${upnl:+,.2f} | Liq: ${liq_price:,.2f}",
                                data={"venue": "aster", "symbol": symbol, "pnl_pct": pnl_pct,
                                      "size": size, "leverage": leverage, "liquidation_price": liq_price},
                            ))

                    # Leverage check
                    if leverage > self.max_leverage:
                        alerts.append(Alert(
                            monitor="position",
                            severity="warning",
                            title=f"Aster {symbol}: {leverage}x leverage exceeds {self.max_leverage}x limit",
                            message=f"Size: {size} | Entry: ${entry:,.2f} | Liq: ${liq_price:,.2f}",
                            data={"venue": "aster", "symbol": symbol, "leverage": leverage},
                        ))
        except Exception as e:
            logger.warning(f"Aster position check failed: {e}")

        return alerts

    def _check_via_agent(self) -> list[Alert]:
        """Fallback: use agent for position check (costs 1-2 LLM calls)."""
        alerts = []
        if not self.agent_chat:
            return alerts

        try:
            response = self.agent_chat(
                "Check my Hyperliquid positions. For each, report: "
                "symbol, side, size, entry price, unrealized PnL, PnL %, leverage. "
                f"Flag anything down more than {self.max_drawdown_pct}% or above {self.max_leverage}x leverage."
            )

            if any(word in response.lower() for word in ["concerning", "exceeds", "risk", "danger", "warning", "down"]):
                alerts.append(Alert(
                    monitor="position",
                    severity="critical",
                    title="⚠️ Position risk detected",
                    message=response[:500],
                    data={"source": "agent_fallback", "full_response": response},
                ))
        except Exception as e:
            logger.error(f"Agent position check failed: {e}")

        return alerts


# ── Sentiment Monitor (Tier 2 with baseline) ─────────────────────────

class SentimentMonitor:
    """
    Tier-2: Uses agent for sentiment, but tracks baseline to detect CHANGES.
    Only alerts when sentiment shifts significantly from previous reading.
    """

    def __init__(self, agent_chat_fn=None):
        self.agent_chat = agent_chat_fn
        self.tracked_topics: list[str] = ["bitcoin", "ethereum", "crypto"]
        self._last_sentiment: dict[str, str] = {}  # topic → "bullish"/"bearish"/"neutral"
        self._sentiment_scores: list[dict] = []     # rolling history

    def check(self) -> list[Alert]:
        """Check sentiment and compare to baseline."""
        alerts = []

        if not self.agent_chat:
            return alerts

        try:
            response = self.agent_chat(
                f"Check sentiment for: {', '.join(self.tracked_topics)}. "
                "Use Y2 news and Elfa social intelligence if available. "
                "For each topic, rate as: bullish, bearish, or neutral. "
                "Also rate confidence: high, medium, low. "
                "Format: TOPIC: SENTIMENT (CONFIDENCE) - brief reason"
            )

            # Parse sentiment from response
            current_sentiment = self._parse_sentiment(response)

            # Compare to baseline — alert on changes
            for topic, sentiment in current_sentiment.items():
                prev = self._last_sentiment.get(topic)
                if prev and prev != sentiment:
                    # Sentiment shifted!
                    severity = "warning" if sentiment in ("bearish", "bullish") else "info"
                    alerts.append(Alert(
                        monitor="sentiment",
                        severity=severity,
                        title=f"📊 {topic.upper()} sentiment: {prev} → {sentiment}",
                        message=f"Sentiment shifted from {prev} to {sentiment}",
                        data={
                            "topic": topic,
                            "previous": prev,
                            "current": sentiment,
                            "analysis": response[:500],
                        },
                    ))

            # If no baseline yet, check for extreme sentiment
            if not self._last_sentiment:
                if any(word in response.lower() for word in ["spike", "surge", "crash", "extreme", "panic"]):
                    alerts.append(Alert(
                        monitor="sentiment",
                        severity="info",
                        title="📊 Significant sentiment signal",
                        message=response[:500],
                        data={"topics": self.tracked_topics},
                    ))

            # Update baseline
            self._last_sentiment = current_sentiment
            self._sentiment_scores.append({
                "timestamp": datetime.now().isoformat(),
                "sentiment": current_sentiment,
            })
            # Keep last 24 readings
            self._sentiment_scores = self._sentiment_scores[-24:]

        except Exception as e:
            logger.error(f"Sentiment monitor error: {e}")
            alerts.append(Alert(
                monitor="sentiment",
                severity="error",
                title="Sentiment Monitor Failed",
                message=f"Monitor check failed: {str(e)[:200]}",
                data={"error": str(e), "error_type": type(e).__name__},
                auto_execute=False,
            ))

        return alerts

    def _parse_sentiment(self, response: str) -> dict[str, str]:
        """Extract sentiment labels from agent response."""
        sentiment = {}
        response_lower = response.lower()
        for topic in self.tracked_topics:
            if topic.lower() in response_lower:
                # Find sentiment near the topic mention
                idx = response_lower.find(topic.lower())
                context = response_lower[idx:idx + 100]
                if "bullish" in context:
                    sentiment[topic] = "bullish"
                elif "bearish" in context:
                    sentiment[topic] = "bearish"
                else:
                    sentiment[topic] = "neutral"
        return sentiment


# ── FRED / Macro Monitor (Tier 1 — direct API) ──────────────────────

class MacroMonitor:
    """
    Tier-1: Direct FRED API for macro-economic data.
    Alerts on regime changes: rate shifts, CPI spikes, employment surprises.
    """

    def __init__(self, agent_chat_fn=None):
        self.agent_chat = agent_chat_fn
        self.fred_key = os.getenv("FRED_API_KEY", "").strip()
        self._last_values: dict[str, float] = {}

        # Key series that move crypto
        self.watched_series = {
            "DFF": {"name": "Fed Funds Rate", "change_threshold": 0.25},
            "CPIAUCSL": {"name": "CPI (All Urban)", "change_threshold": 0.3},
            "UNRATE": {"name": "Unemployment Rate", "change_threshold": 0.2},
            "T10Y2Y": {"name": "10Y-2Y Spread", "change_threshold": 0.1},
            "VIXCLS": {"name": "VIX", "change_threshold": 5.0},
        }

    def check(self) -> list[Alert]:
        """Tier-1: Direct FRED API, no LLM."""
        alerts = []

        if not self.fred_key:
            return alerts

        try:
            import requests

            for series_id, config in self.watched_series.items():
                resp = requests.get(
                    "https://api.stlouisfed.org/fred/series/observations",
                    params={
                        "series_id": series_id,
                        "api_key": self.fred_key,
                        "file_type": "json",
                        "sort_order": "desc",
                        "limit": 2,
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()

                obs = data.get("observations", [])
                if len(obs) < 2:
                    continue

                current = float(obs[0]["value"]) if obs[0]["value"] != "." else None
                previous = float(obs[1]["value"]) if obs[1]["value"] != "." else None

                if current is None or previous is None:
                    continue

                change = current - previous
                self._last_values[series_id] = current

                # Check threshold
                if abs(change) >= config["change_threshold"]:
                    direction = "📈" if change > 0 else "📉"
                    alerts.append(Alert(
                        monitor="macro",
                        severity="warning",
                        title=f"{direction} {config['name']}: {previous:.2f} → {current:.2f}",
                        message=(
                            f"{config['name']} changed by {change:+.2f} "
                            f"(threshold: ±{config['change_threshold']})"
                        ),
                        data={
                            "series": series_id,
                            "name": config["name"],
                            "current": current,
                            "previous": previous,
                            "change": change,
                        },
                    ))

        except Exception as e:
            logger.error(f"Macro monitor error: {e}")
            alerts.append(Alert(
                monitor="macro",
                severity="error",
                title="Macro Monitor Failed",
                message=f"Monitor check failed: {str(e)[:200]}",
                data={"error": str(e), "error_type": type(e).__name__},
                auto_execute=False,
            ))

        return alerts
