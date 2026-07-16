"""Technical analysis tools: moving averages, RSI, MACD, trend."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import yfinance as yf


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    # A zero average loss means no down days in the window (maximally bullish);
    # the division above yields NaN there instead of the conventional RSI of 100.
    return rsi.mask(avg_loss == 0, 100)


def compute_technical_indicators(ticker: str, period: str = "6mo") -> str:
    """Compute technical indicators (SMA20, SMA50, RSI14, MACD, trend) from recent price history."""
    t = yf.Ticker(ticker)
    try:
        hist = t.history(period=period, interval="1d")
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"Could not fetch history for {ticker}: {exc}"})

    if hist.empty or len(hist) < 20:
        return json.dumps({"error": f"Not enough historical data for {ticker} to compute indicators"})

    close = hist["Close"]
    sma20 = _sma(close, 20)
    sma50 = _sma(close, 50) if len(close) >= 50 else None
    rsi14 = _rsi(close, 14)

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()

    last_close = float(close.iloc[-1])
    last_sma20 = float(sma20.iloc[-1])
    last_rsi = float(rsi14.iloc[-1])

    payload = {
        "ticker": ticker.upper(),
        "period": period,
        "last_close": round(last_close, 2),
        "sma_20": round(last_sma20, 2) if not np.isnan(last_sma20) else None,
        "sma_50": (
            round(float(sma50.iloc[-1]), 2)
            if sma50 is not None and not np.isnan(sma50.iloc[-1])
            else None
        ),
        "rsi_14": round(last_rsi, 2) if not np.isnan(last_rsi) else None,
        "macd": round(float(macd_line.iloc[-1]), 3),
        "macd_signal": round(float(signal_line.iloc[-1]), 3),
        "macd_histogram": round(float(macd_line.iloc[-1] - signal_line.iloc[-1]), 3),
        "price_vs_sma20": (
            "above" if not np.isnan(last_sma20) and last_close > last_sma20 else "below"
        ),
        "trend_20d": "up" if len(close) > 20 and close.iloc[-1] > close.iloc[-20] else "down",
    }
    return json.dumps(payload)
