"""Risk assessment tools: volatility, drawdown, beta, Sharpe ratio, VaR."""

from __future__ import annotations

import json

import numpy as np
import yfinance as yf

TRADING_DAYS_PER_YEAR = 252
ASSUMED_RISK_FREE_RATE = 0.04


def compute_risk_metrics(ticker: str, period: str = "1y", benchmark: str = "^GSPC") -> str:
    """Compute risk metrics: annualized volatility, beta vs benchmark, max drawdown, Sharpe ratio, 95% VaR."""
    t = yf.Ticker(ticker)
    try:
        hist = t.history(period=period, interval="1d")
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"Could not fetch history for {ticker}: {exc}"})

    if hist.empty or len(hist) < 30:
        return json.dumps({"error": f"Not enough historical data for {ticker} to compute risk metrics"})

    returns = hist["Close"].pct_change().dropna()
    ann_vol = float(returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR))

    cummax = hist["Close"].cummax()
    drawdown = (hist["Close"] - cummax) / cummax
    max_drawdown = float(drawdown.min())

    mean_daily_return = float(returns.mean())
    ann_return = mean_daily_return * TRADING_DAYS_PER_YEAR
    sharpe = (ann_return - ASSUMED_RISK_FREE_RATE) / ann_vol if ann_vol else None

    var_95 = float(np.percentile(returns, 5))

    beta = None
    try:
        bench_hist = yf.Ticker(benchmark).history(period=period, interval="1d")
        bench_returns = bench_hist["Close"].pct_change().dropna()
        aligned_asset, aligned_bench = returns.align(bench_returns, join="inner")
        if len(aligned_asset) > 10:
            covariance = np.cov(aligned_asset, aligned_bench)[0][1]
            variance = np.var(aligned_bench)
            beta = float(covariance / variance) if variance else None
    except Exception:  # noqa: BLE001 - beta is a nice-to-have, not essential
        beta = None

    payload = {
        "ticker": ticker.upper(),
        "period": period,
        "annualized_volatility_percent": round(ann_vol * 100, 2),
        "annualized_return_percent": round(ann_return * 100, 2),
        "max_drawdown_percent": round(max_drawdown * 100, 2),
        "sharpe_ratio": round(sharpe, 2) if sharpe is not None else None,
        "value_at_risk_95_daily_percent": round(var_95 * 100, 2),
        "beta_vs_benchmark": round(beta, 2) if beta is not None else None,
        "benchmark": benchmark,
    }
    return json.dumps(payload)
