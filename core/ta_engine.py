"""
TA Engine — Technical Analysis for Sentinel Trading System

Uses pandas-ta for indicator computation on Aster DEX kline data.
Provides SMA/EMA/RSI/MACD/Bollinger Bands + crossover detection.

Usage:
    from ta_engine import compute_sma, compute_indicators, detect_crossover
    df = compute_sma("BTCUSDT", fast=9, slow=21, interval="5m")
    signal = detect_crossover(df)  # "bullish", "bearish", or None
"""

import logging
from typing import Optional

import pandas as pd

try:
    import pandas_ta as ta
except ImportError:
    ta = None

from scrapers.aster_scraper import aster_klines

logger = logging.getLogger("sentinel.ta_engine")


def klines_to_df(symbol: str, interval: str = "5m", limit: int = 100) -> Optional[pd.DataFrame]:
    """Fetch Aster klines and convert to a pandas DataFrame."""
    raw = aster_klines(symbol, interval=interval, limit=limit)

    if isinstance(raw, dict) and raw.get("error"):
        logger.error(f"Klines fetch failed for {symbol}: {raw['error']}")
        return None

    if not raw or len(raw) < 2:
        logger.warning(f"Insufficient kline data for {symbol}: got {len(raw) if raw else 0} candles")
        return None

    df = pd.DataFrame(raw)
    # Ensure numeric types
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df


def compute_sma(
    symbol: str,
    fast: int = 9,
    slow: int = 21,
    interval: str = "5m",
    limit: int = 100,
) -> Optional[pd.DataFrame]:
    """
    Compute fast and slow SMA for a symbol.

    Returns DataFrame with columns: close, sma_fast, sma_slow, crossover.
    crossover: 1 = bullish cross (fast above slow), -1 = bearish, 0 = no cross.
    """
    df = klines_to_df(symbol, interval=interval, limit=limit)
    if df is None:
        return None

    if ta:
        df["sma_fast"] = ta.sma(df["close"], length=fast)
        df["sma_slow"] = ta.sma(df["close"], length=slow)
    else:
        # Fallback: manual SMA computation
        df["sma_fast"] = df["close"].rolling(window=fast).mean()
        df["sma_slow"] = df["close"].rolling(window=slow).mean()

    # Detect crossover: fast crosses above slow = 1, below = -1
    df["cross_diff"] = df["sma_fast"] - df["sma_slow"]
    df["cross_prev"] = df["cross_diff"].shift(1)
    df["crossover"] = 0
    df.loc[(df["cross_diff"] > 0) & (df["cross_prev"] <= 0), "crossover"] = 1   # bullish
    df.loc[(df["cross_diff"] < 0) & (df["cross_prev"] >= 0), "crossover"] = -1  # bearish

    return df


def compute_indicators(
    symbol: str,
    interval: str = "5m",
    limit: int = 100,
) -> Optional[dict]:
    """
    Compute a full suite of indicators for a symbol.

    Returns dict with latest values for: SMA(9), SMA(21), EMA(12), EMA(26),
    RSI(14), MACD, Bollinger Bands, and the current price.
    """
    df = klines_to_df(symbol, interval=interval, limit=limit)
    if df is None:
        return None

    result = {
        "symbol": symbol,
        "interval": interval,
        "price": float(df["close"].iloc[-1]),
        "candles": len(df),
    }

    if ta:
        # SMAs
        sma9 = ta.sma(df["close"], length=9)
        sma21 = ta.sma(df["close"], length=21)
        result["sma_9"] = float(sma9.iloc[-1]) if sma9 is not None and not sma9.empty else None
        result["sma_21"] = float(sma21.iloc[-1]) if sma21 is not None and not sma21.empty else None

        # EMAs
        ema12 = ta.ema(df["close"], length=12)
        ema26 = ta.ema(df["close"], length=26)
        result["ema_12"] = float(ema12.iloc[-1]) if ema12 is not None and not ema12.empty else None
        result["ema_26"] = float(ema26.iloc[-1]) if ema26 is not None and not ema26.empty else None

        # RSI
        rsi = ta.rsi(df["close"], length=14)
        result["rsi_14"] = float(rsi.iloc[-1]) if rsi is not None and not rsi.empty else None

        # MACD
        macd = ta.macd(df["close"])
        if macd is not None and not macd.empty:
            result["macd"] = float(macd.iloc[-1, 0])
            result["macd_signal"] = float(macd.iloc[-1, 1])
            result["macd_histogram"] = float(macd.iloc[-1, 2])

        # Bollinger Bands
        bbands = ta.bbands(df["close"], length=20)
        if bbands is not None and not bbands.empty:
            result["bb_upper"] = float(bbands.iloc[-1, 0])
            result["bb_mid"] = float(bbands.iloc[-1, 1])
            result["bb_lower"] = float(bbands.iloc[-1, 2])
    else:
        # Minimal fallback without pandas-ta
        result["sma_9"] = float(df["close"].rolling(9).mean().iloc[-1])
        result["sma_21"] = float(df["close"].rolling(21).mean().iloc[-1])
        result["rsi_14"] = None
        result["note"] = "pandas-ta not installed — only SMA available"

    return result


def detect_crossover(df: Optional[pd.DataFrame]) -> Optional[str]:
    """
    Check the most recent candle for a crossover signal.

    Returns:
        "bullish"  — fast SMA just crossed ABOVE slow SMA
        "bearish"  — fast SMA just crossed BELOW slow SMA
        None       — no crossover on the latest candle
    """
    if df is None or "crossover" not in df.columns:
        return None

    latest = df["crossover"].iloc[-1]
    if latest == 1:
        return "bullish"
    elif latest == -1:
        return "bearish"
    return None


def get_ta_summary(symbol: str, interval: str = "5m") -> dict:
    """
    One-call summary: indicators + crossover signal.
    Designed to be used as an agent tool.
    """
    indicators = compute_indicators(symbol, interval=interval)
    if not indicators:
        return {"error": f"Failed to compute TA for {symbol}"}

    sma_df = compute_sma(symbol, interval=interval)
    signal = detect_crossover(sma_df)

    indicators["sma_crossover_signal"] = signal or "neutral"

    # Human-readable summary
    rsi = indicators.get("rsi_14")
    if rsi:
        if rsi > 70:
            indicators["rsi_signal"] = "overbought"
        elif rsi < 30:
            indicators["rsi_signal"] = "oversold"
        else:
            indicators["rsi_signal"] = "neutral"

    return indicators
