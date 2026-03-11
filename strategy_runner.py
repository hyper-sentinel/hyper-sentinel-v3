"""
Strategy Runner — Autonomous SMA Crossover Trading for Sentinel

Called by the Scheduler on a timer. Fetches klines, computes TA,
detects SMA crossovers, and executes trades through Aster DEX —
all gated by Sentinel's Guardrails.

Config via .env:
    STRATEGY_SYMBOL=BTCUSDT
    STRATEGY_INTERVAL=5m
    STRATEGY_FAST_SMA=9
    STRATEGY_SLOW_SMA=21
    STRATEGY_TRADE_USD=25
    STRATEGY_ENABLED=false
"""

import os
import json
import logging
from datetime import datetime

from ta_engine import compute_sma, detect_crossover, compute_indicators
from scrapers.aster_scraper import aster_ticker, aster_place_order, aster_positions

logger = logging.getLogger("sentinel.strategy")


class StrategyRunner:
    """
    SMA Crossover Strategy — runs on a scheduler timer.

    Flow:
        1. Fetch klines → compute SMA(fast) and SMA(slow)
        2. Detect crossover on latest candle
        3. Check Guardrails (trade limits, kill switch)
        4. Execute trade via Aster
        5. Notify via Telegram/log
    """

    def __init__(self, guardrails, notifier):
        self.guardrails = guardrails
        self.notifier = notifier

        # Config from .env
        self.symbol = os.getenv("STRATEGY_SYMBOL", "BTCUSDT")
        self.interval = os.getenv("STRATEGY_INTERVAL", "5m")
        self.fast_sma = int(os.getenv("STRATEGY_FAST_SMA", "9"))
        self.slow_sma = int(os.getenv("STRATEGY_SLOW_SMA", "21"))
        self.trade_usd = float(os.getenv("STRATEGY_TRADE_USD", "25"))
        self.enabled = os.getenv("STRATEGY_ENABLED", "false").lower() == "true"

        # State tracking
        self.last_signal = None
        self.last_run = None
        self.run_count = 0
        self.trades_executed = []
        self._current_position = None  # "long", "short", or None

    def run(self):
        """Main entry point — called by the Scheduler."""
        self.run_count += 1
        self.last_run = datetime.now().isoformat()

        if not self.enabled:
            logger.debug("Strategy disabled — skipping")
            return

        try:
            self._execute_strategy()
        except Exception as e:
            logger.error(f"Strategy run failed: {e}")
            self.notifier.send_sync(
                f"⚠️ Strategy error: {e}", channel="strategy"
            )

    def _execute_strategy(self):
        """Core strategy logic."""
        # 1. Compute SMA
        df = compute_sma(
            self.symbol,
            fast=self.fast_sma,
            slow=self.slow_sma,
            interval=self.interval,
            limit=max(self.slow_sma * 3, 50),
        )

        if df is None:
            logger.warning(f"No data for {self.symbol} — skipping")
            return

        # 2. Detect crossover
        signal = detect_crossover(df)

        if not signal:
            logger.debug(f"No crossover on {self.symbol} — holding")
            return

        # Skip duplicate signals
        if signal == self.last_signal:
            logger.debug(f"Signal {signal} already acted on — skipping")
            return

        self.last_signal = signal
        price = float(df["close"].iloc[-1])
        sma_fast = float(df["sma_fast"].iloc[-1])
        sma_slow = float(df["sma_slow"].iloc[-1])

        logger.info(
            f"🔔 {signal.upper()} crossover on {self.symbol} @ ${price:.2f} "
            f"(SMA{self.fast_sma}={sma_fast:.2f} vs SMA{self.slow_sma}={sma_slow:.2f})"
        )

        # 3. Determine action
        if signal == "bullish":
            side = "BUY"
            # Close short if in one, then go long
            if self._current_position == "short":
                self._close_position("Bullish cross — closing short")
        elif signal == "bearish":
            side = "SELL"
            # Close long if in one, then go short
            if self._current_position == "long":
                self._close_position("Bearish cross — closing long")
        else:
            return

        # 4. Check Guardrails
        can_exec, reason = self.guardrails.can_execute(self.trade_usd)
        if not can_exec:
            msg = (
                f"🚫 Trade blocked by guardrails: {reason}\n"
                f"Signal: {signal} on {self.symbol} @ ${price:.2f}"
            )
            logger.warning(msg)
            self.notifier.send_sync(msg, channel="strategy")
            return

        # 5. Calculate quantity from USD amount
        quantity = self.trade_usd / price

        # 6. Execute trade
        logger.info(f"Executing {side} {quantity:.6f} {self.symbol} (~${self.trade_usd})")

        result = aster_place_order(
            symbol=self.symbol,
            side=side,
            order_type="MARKET",
            quantity=quantity,
        )

        # 7. Record and notify
        self.guardrails.record_trade()
        self._current_position = "long" if side == "BUY" else "short"

        trade_record = {
            "time": datetime.now().isoformat(),
            "signal": signal,
            "side": side,
            "symbol": self.symbol,
            "price": price,
            "quantity": quantity,
            "usd_value": self.trade_usd,
            "result": result,
        }
        self.trades_executed.append(trade_record)

        msg = (
            f"🤖 Auto-Trade Executed\n"
            f"Signal: {signal.upper()} crossover\n"
            f"Pair: {self.symbol}\n"
            f"Side: {side}\n"
            f"Price: ${price:,.2f}\n"
            f"Size: {quantity:.6f} (~${self.trade_usd})\n"
            f"SMA({self.fast_sma}): {sma_fast:.2f}\n"
            f"SMA({self.slow_sma}): {sma_slow:.2f}\n"
            f"Result: {json.dumps(result)[:200]}"
        )
        self.notifier.send_sync(msg, channel="trades")
        logger.info(msg)

    def _close_position(self, reason: str):
        """Close the current position before flipping sides."""
        if not self._current_position:
            return

        close_side = "SELL" if self._current_position == "long" else "BUY"
        logger.info(f"Closing {self._current_position} position: {reason}")

        # Get current positions to find exact size
        positions = aster_positions()
        if isinstance(positions, list):
            for pos in positions:
                if pos.get("symbol", "").upper() == self.symbol.upper():
                    qty = abs(float(pos.get("positionAmt", 0)))
                    if qty > 0:
                        aster_place_order(
                            symbol=self.symbol,
                            side=close_side,
                            order_type="MARKET",
                            quantity=qty,
                        )
                        self.guardrails.record_trade()

        self._current_position = None

    def status(self) -> dict:
        """Return current strategy state — used by /status endpoint and agent."""
        return {
            "enabled": self.enabled,
            "symbol": self.symbol,
            "interval": self.interval,
            "sma_fast": self.fast_sma,
            "sma_slow": self.slow_sma,
            "trade_usd": self.trade_usd,
            "last_signal": self.last_signal,
            "last_run": self.last_run,
            "run_count": self.run_count,
            "current_position": self._current_position,
            "recent_trades": self.trades_executed[-5:],
        }
