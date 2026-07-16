"""Market data tools backed by Yahoo Finance (via yfinance)."""

from __future__ import annotations

import json

import yfinance as yf


def get_stock_price(ticker: str) -> str:
    """Get the latest price, day change, and volume for a ticker."""
    t = yf.Ticker(ticker)
    try:
        fast = t.fast_info
        price = fast["lastPrice"]
        prev_close = fast["previousClose"]
        change = price - prev_close
        pct = (change / prev_close * 100) if prev_close else 0.0
        payload = {
            "ticker": ticker.upper(),
            "price": round(price, 2),
            "previous_close": round(prev_close, 2),
            "change": round(change, 2),
            "change_percent": round(pct, 2),
            "day_high": round(fast.get("dayHigh", 0) or 0, 2),
            "day_low": round(fast.get("dayLow", 0) or 0, 2),
            "volume": fast.get("lastVolume"),
            "market_cap": fast.get("marketCap"),
            "currency": fast.get("currency"),
        }
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"Could not fetch price for {ticker}: {exc}"})
    return json.dumps(payload)


def get_company_info(ticker: str) -> str:
    """Get company profile: sector, industry, description, market cap."""
    t = yf.Ticker(ticker)
    try:
        info = t.info or {}
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"Could not fetch company info for {ticker}: {exc}"})

    if not info.get("longName") and not info.get("shortName"):
        return json.dumps({"error": f"No company info found for {ticker}"})

    payload = {
        "ticker": ticker.upper(),
        "name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "employees": info.get("fullTimeEmployees"),
        "market_cap": info.get("marketCap"),
        "summary": (info.get("longBusinessSummary") or "")[:1200],
        "website": info.get("website"),
    }
    return json.dumps(payload)


def get_historical_prices(ticker: str, period: str = "6mo", interval: str = "1d") -> str:
    """Get historical OHLCV summary statistics for a ticker over a period.

    `period` examples: 1mo, 3mo, 6mo, 1y, 5y, max. `interval` examples: 1d, 1wk, 1mo.
    """
    t = yf.Ticker(ticker)
    try:
        hist = t.history(period=period, interval=interval)
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"Could not fetch history for {ticker}: {exc}"})

    if hist.empty:
        return json.dumps({"error": f"No historical data for {ticker}"})

    closes = hist["Close"]
    payload = {
        "ticker": ticker.upper(),
        "period": period,
        "interval": interval,
        "num_periods": len(hist),
        "start_date": str(hist.index[0].date()),
        "end_date": str(hist.index[-1].date()),
        "start_price": round(float(closes.iloc[0]), 2),
        "end_price": round(float(closes.iloc[-1]), 2),
        "period_return_percent": round(float((closes.iloc[-1] / closes.iloc[0] - 1) * 100), 2),
        "period_high": round(float(hist["High"].max()), 2),
        "period_low": round(float(hist["Low"].min()), 2),
        "avg_volume": int(hist["Volume"].mean()),
        "recent_closes": [round(float(c), 2) for c in closes.tail(10)],
    }
    return json.dumps(payload)


def get_analyst_recommendations(ticker: str) -> str:
    """Get recent Wall Street analyst recommendation ratings for a ticker."""
    t = yf.Ticker(ticker)
    try:
        rec = t.recommendations
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)})

    if rec is None or rec.empty:
        return json.dumps({"error": f"No analyst recommendations for {ticker}"})

    latest = rec.tail(6).to_dict(orient="records")
    return json.dumps({"ticker": ticker.upper(), "recent_recommendations": latest}, default=str)
