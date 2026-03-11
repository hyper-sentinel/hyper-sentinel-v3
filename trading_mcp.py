"""
Custom Trading MCP Server — Expose portfolio aggregation tools via MCP.

Run: python trading_mcp.py
Or import in swarm.py as: MCPTools(command=sys.executable, args=["trading_mcp.py"])

Provides cross-venue portfolio tools that no single API offers:
  • get_portfolio_summary — Aggregate positions across HL + Aster + Polymarket
  • calculate_position_size — Risk-based position sizing
  • get_venue_status — Check which venues are connected
  • get_risk_metrics — Portfolio-level risk calculations
"""

import os
from dotenv import load_dotenv

load_dotenv()

from fastmcp import FastMCP

mcp = FastMCP("HyperTrading", instructions="Cross-venue portfolio management and risk tools for Hyper Sentinel.")


@mcp.tool()
def get_portfolio_summary() -> dict:
    """Get combined portfolio summary across all trading venues (Hyperliquid, Aster, Polymarket)."""
    summary = {"venues": {}, "total_equity": 0, "total_unrealized_pnl": 0}

    # Hyperliquid
    try:
        from scrapers.hyperliquid_scraper import get_hl_account, get_hl_positions
        account = get_hl_account()
        positions = get_hl_positions()
        hl_equity = float(account.get("accountValue", 0)) if isinstance(account, dict) else 0
        summary["venues"]["hyperliquid"] = {
            "equity": hl_equity,
            "positions": len(positions) if isinstance(positions, list) else 0,
            "status": "connected",
        }
        summary["total_equity"] += hl_equity
    except Exception as e:
        summary["venues"]["hyperliquid"] = {"status": f"error: {e}"}

    # Aster DEX
    try:
        from scrapers.aster_scraper import aster_balance
        balance = aster_balance()
        aster_equity = float(balance.get("totalWalletBalance", 0)) if isinstance(balance, dict) else 0
        summary["venues"]["aster"] = {
            "equity": aster_equity,
            "status": "connected",
        }
        summary["total_equity"] += aster_equity
    except Exception as e:
        summary["venues"]["aster"] = {"status": f"error: {e}"}

    # Polymarket
    try:
        from scrapers.polymarket_scraper import get_polymarket_positions
        positions = get_polymarket_positions()
        summary["venues"]["polymarket"] = {
            "positions": len(positions) if isinstance(positions, list) else 0,
            "status": "connected",
        }
    except Exception as e:
        summary["venues"]["polymarket"] = {"status": f"error: {e}"}

    return summary


@mcp.tool()
def calculate_position_size(
    account_equity: float,
    risk_percent: float = 2.0,
    stop_loss_distance_percent: float = 5.0,
    max_leverage: float = 10.0,
) -> dict:
    """Calculate optimal position size based on risk parameters.

    Args:
        account_equity: Total account equity in USD.
        risk_percent: Max % of equity to risk on this trade (default 2%).
        stop_loss_distance_percent: Distance to stop loss as % of entry (default 5%).
        max_leverage: Maximum allowable leverage (default 10x).
    """
    risk_amount = account_equity * (risk_percent / 100)
    position_size = risk_amount / (stop_loss_distance_percent / 100)
    leverage_needed = position_size / account_equity if account_equity > 0 else 0

    return {
        "account_equity": account_equity,
        "risk_amount_usd": round(risk_amount, 2),
        "position_size_usd": round(position_size, 2),
        "leverage_needed": round(leverage_needed, 2),
        "leverage_capped": min(round(leverage_needed, 2), max_leverage),
        "stop_loss_distance": f"{stop_loss_distance_percent}%",
        "risk_per_trade": f"{risk_percent}%",
        "warning": "OVER-LEVERAGED" if leverage_needed > max_leverage else "OK",
    }


@mcp.tool()
def get_venue_status() -> dict:
    """Check connection status of all trading venues."""
    status = {}

    # Hyperliquid
    hl_wallet = os.getenv("HYPERLIQUID_WALLET_ADDRESS", "").strip()
    hl_key = os.getenv("HYPERLIQUID_PRIVATE_KEY", "").strip()
    if hl_key:
        status["hyperliquid"] = {"status": "trading_enabled", "wallet": hl_wallet[:10] + "..."}
    elif hl_wallet:
        status["hyperliquid"] = {"status": "read_only", "wallet": hl_wallet[:10] + "..."}
    else:
        status["hyperliquid"] = {"status": "not_configured"}

    # Aster DEX
    aster_key = os.getenv("ASTER_API_KEY", "").strip()
    aster_secret = os.getenv("ASTER_API_SECRET", "").strip()
    if aster_key and aster_secret:
        status["aster"] = {"status": "trading_enabled"}
    else:
        status["aster"] = {"status": "market_data_only"}

    # Polymarket
    pm_key = os.getenv("POLYMARKET_PRIVATE_KEY", "").strip()
    if pm_key:
        status["polymarket"] = {"status": "trading_enabled"}
    else:
        status["polymarket"] = {"status": "read_only"}

    # FRED
    fred_key = os.getenv("FRED_API_KEY", "").strip()
    status["fred"] = {"status": "connected" if fred_key else "not_configured"}

    return status


@mcp.tool()
def get_risk_metrics(
    account_equity: float,
    total_position_value: float,
    unrealized_pnl: float,
    max_drawdown_threshold: float = 10.0,
) -> dict:
    """Calculate portfolio-level risk metrics.

    Args:
        account_equity: Total account equity.
        total_position_value: Sum of all position notional values.
        unrealized_pnl: Current unrealized PnL.
        max_drawdown_threshold: Alert if drawdown exceeds this % (default 10%).
    """
    leverage = total_position_value / account_equity if account_equity > 0 else 0
    drawdown_pct = (unrealized_pnl / account_equity * 100) if account_equity > 0 and unrealized_pnl < 0 else 0
    utilization = (total_position_value / account_equity * 100) if account_equity > 0 else 0

    alerts = []
    if leverage > 3:
        alerts.append(f"HIGH LEVERAGE: {leverage:.1f}x (threshold: 3x)")
    if abs(drawdown_pct) > max_drawdown_threshold:
        alerts.append(f"DRAWDOWN ALERT: {drawdown_pct:.1f}% (threshold: {max_drawdown_threshold}%)")
    if utilization > 80:
        alerts.append(f"HIGH UTILIZATION: {utilization:.1f}% of equity deployed")

    return {
        "portfolio_leverage": round(leverage, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "drawdown_percent": round(drawdown_pct, 2),
        "margin_utilization_percent": round(utilization, 2),
        "risk_level": "🔴 HIGH" if alerts else "🟢 NORMAL",
        "alerts": alerts if alerts else ["No risk alerts"],
    }


if __name__ == "__main__":
    mcp.run()
