"""
Webhook Server — TradingView Alert Receiver for Sentinel

FastAPI server that receives TradingView webhook alerts and executes
trades through Aster DEX, gated by Sentinel's Guardrails.

Config via .env:
    WEBHOOK_PORT=8888
    WEBHOOK_SECRET=your-secret-token
    WEBHOOK_ENABLED=false

TradingView alert message format (JSON):
    {
        "secret": "your-secret-token",
        "action": "buy" | "sell" | "close",
        "symbol": "BTCUSDT",
        "size_usd": 50,
        "source": "SMA_Cross_5m"
    }

Run standalone: python webhook_server.py
Or auto-started by sentinel.py in a background thread.
"""

import os
import json
import logging
import threading
from datetime import datetime
from typing import Optional

logger = logging.getLogger("sentinel.webhook")

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    logger.warning("FastAPI not installed — webhook server unavailable. Run: pip install fastapi uvicorn")

from scrapers.aster_scraper import aster_place_order


class WebhookServer:
    """
    TradingView webhook receiver with guardrail enforcement.

    Runs in a background thread so it doesn't block the Sentinel main loop.
    """

    def __init__(self, guardrails, notifier, strategy_runner=None):
        self.guardrails = guardrails
        self.notifier = notifier
        self.strategy_runner = strategy_runner

        self.port = int(os.getenv("WEBHOOK_PORT", "8888"))
        self.secret = os.getenv("WEBHOOK_SECRET", "sentinel-webhook-secret")
        self.enabled = os.getenv("WEBHOOK_ENABLED", "false").lower() == "true"

        self._thread: Optional[threading.Thread] = None
        self._app: Optional[object] = None

        # Trade log
        self.webhook_trades = []
        self.webhook_count = 0

    def _create_app(self):
        """Build the FastAPI application."""
        if not HAS_FASTAPI:
            return None

        app = FastAPI(
            title="Sentinel Webhook Server",
            description="Receives TradingView alerts for autonomous trading",
            version="1.0.0",
        )

        @app.get("/health")
        async def health():
            return {
                "status": "ok",
                "service": "sentinel-webhook",
                "enabled": self.enabled,
                "uptime_webhooks": self.webhook_count,
            }

        @app.get("/status")
        async def status():
            return {
                "webhook": {
                    "enabled": self.enabled,
                    "port": self.port,
                    "total_received": self.webhook_count,
                    "recent_trades": self.webhook_trades[-5:],
                },
                "guardrails": self.guardrails.status(),
                "strategy": self.strategy_runner.status() if self.strategy_runner else None,
            }

        @app.post("/webhook")
        async def webhook(request: Request):
            self.webhook_count += 1

            if not self.enabled:
                return JSONResponse(
                    status_code=403,
                    content={"error": "Webhook trading disabled"},
                )

            # Parse body
            try:
                body = await request.json()
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON")

            # Validate secret
            if body.get("secret") != self.secret:
                logger.warning(f"Webhook rejected — invalid secret")
                raise HTTPException(status_code=401, detail="Invalid secret")

            # Extract signal
            action = body.get("action", "").lower()
            symbol = body.get("symbol", "BTCUSDT").upper()
            size_usd = float(body.get("size_usd", 25))
            source = body.get("source", "tradingview")

            if action not in ("buy", "sell", "close"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid action: {action}. Must be buy, sell, or close.",
                )

            logger.info(f"📡 Webhook received: {action} {symbol} ${size_usd} from {source}")

            # Check guardrails
            can_exec, reason = self.guardrails.can_execute(size_usd)
            if not can_exec:
                msg = f"🚫 Webhook trade blocked: {reason}"
                logger.warning(msg)
                self.notifier.send_sync(msg, channel="webhook")
                return {"status": "blocked", "reason": reason}

            # Execute trade
            if action == "close":
                # Close all positions on this symbol
                result = self._close_position(symbol)
            else:
                side = "BUY" if action == "buy" else "SELL"

                result = aster_place_order(
                    symbol=symbol,
                    side=side,
                    order_type="MARKET",
                    usd_amount=size_usd,
                )

            # Record
            self.guardrails.record_trade()
            trade_record = {
                "time": datetime.now().isoformat(),
                "action": action,
                "symbol": symbol,
                "size_usd": size_usd,
                "source": source,
                "result": result,
            }
            self.webhook_trades.append(trade_record)

            # Notify
            msg = (
                f"📡 Webhook Trade Executed\n"
                f"Source: {source}\n"
                f"Action: {action.upper()}\n"
                f"Symbol: {symbol}\n"
                f"Size: ~${size_usd}\n"
                f"Result: {json.dumps(result)[:200]}"
            )
            self.notifier.send_sync(msg, channel="trades")

            return {"status": "executed", "trade": trade_record}

        self._app = app
        return app

    def _close_position(self, symbol: str) -> dict:
        """Close all positions on a symbol."""
        from scrapers.aster_scraper import aster_positions

        positions = aster_positions()
        if isinstance(positions, dict) and positions.get("error"):
            return positions

        closed = []
        if isinstance(positions, list):
            for pos in positions:
                if pos.get("symbol", "").upper() == symbol.upper():
                    qty = abs(float(pos.get("positionAmt", 0)))
                    if qty > 0:
                        side = "SELL" if float(pos.get("positionAmt", 0)) > 0 else "BUY"
                        result = aster_place_order(
                            symbol=symbol,
                            side=side,
                            order_type="MARKET",
                            quantity=qty,
                        )
                        closed.append(result)

        return {"closed_positions": len(closed), "results": closed}

    def start(self):
        """Start the webhook server in a background thread."""
        if not HAS_FASTAPI:
            logger.warning("Cannot start webhook server — FastAPI not installed")
            return False

        if not self.enabled:
            logger.info("Webhook server disabled (WEBHOOK_ENABLED=false)")
            return False

        app = self._create_app()
        if not app:
            return False

        def _run():
            uvicorn.run(app, host="0.0.0.0", port=self.port, log_level="warning")

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        logger.info(f"Webhook server started on port {self.port}")
        return True

    def stop(self):
        """Stop the webhook server (if running)."""
        # uvicorn doesn't have a clean stop from threads — daemon thread will
        # die when main process exits
        logger.info("Webhook server stopping")


# ── Standalone mode ──────────────────────────────────────────────────

if __name__ == "__main__":
    from sentinel import Guardrails, Notifier

    guardrails = Guardrails()
    notifier = Notifier()
    server = WebhookServer(guardrails, notifier)
    server.enabled = True  # Force enable for standalone testing

    if HAS_FASTAPI:
        app = server._create_app()
        print(f"🚀 Webhook server running on http://0.0.0.0:{server.port}")
        print(f"   POST /webhook — receive TradingView alerts")
        print(f"   GET  /health  — health check")
        print(f"   GET  /status  — full status")
        uvicorn.run(app, host="0.0.0.0", port=server.port)
    else:
        print("❌ FastAPI not installed. Run: pip install fastapi uvicorn")
