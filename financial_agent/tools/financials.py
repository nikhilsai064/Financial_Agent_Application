"""Fundamental analysis tools: financial statements and valuation ratios."""

from __future__ import annotations

import json

import yfinance as yf


def _df_to_summary(df, n_periods: int = 4) -> dict:
    """Convert a yfinance statement DataFrame (rows=line items, cols=periods) to a small dict."""
    if df is None or df.empty:
        return {}
    df = df.iloc[:, :n_periods]
    out: dict[str, dict[str, float | None]] = {}
    for row_label, row in df.iterrows():
        period_values: dict[str, float | None] = {}
        for col, value in row.items():
            col_label = str(col.date()) if hasattr(col, "date") else str(col)
            period_values[col_label] = None if value != value else round(float(value), 2)  # noqa: PLR0124 - NaN check
        out[str(row_label)] = period_values
    return out


def get_income_statement(ticker: str) -> str:
    """Get a summary of recent annual income statement line items (revenue, net income, margins)."""
    t = yf.Ticker(ticker)
    try:
        fin = t.financials
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)})

    if fin is None or fin.empty:
        return json.dumps({"error": f"No income statement for {ticker}"})

    keys = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income", "EBITDA"]
    key_rows = [row for row in fin.index if any(k in row for k in keys)]
    summary = _df_to_summary(fin.loc[fin.index.isin(key_rows)])
    return json.dumps({"ticker": ticker.upper(), "income_statement": summary})


def get_balance_sheet(ticker: str) -> str:
    """Get a summary of recent annual balance sheet line items (assets, liabilities, equity, debt)."""
    t = yf.Ticker(ticker)
    try:
        bs = t.balance_sheet
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)})

    if bs is None or bs.empty:
        return json.dumps({"error": f"No balance sheet for {ticker}"})

    keys = [
        "Total Assets",
        "Total Liabilities Net Minority Interest",
        "Total Equity Gross Minority Interest",
        "Total Debt",
        "Cash And Cash Equivalents",
        "Working Capital",
    ]
    key_rows = [row for row in bs.index if any(k in row for k in keys)]
    summary = _df_to_summary(bs.loc[bs.index.isin(key_rows)])
    return json.dumps({"ticker": ticker.upper(), "balance_sheet": summary})


def get_cash_flow(ticker: str) -> str:
    """Get a summary of recent annual cash flow line items (operating, investing, financing, FCF)."""
    t = yf.Ticker(ticker)
    try:
        cf = t.cashflow
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)})

    if cf is None or cf.empty:
        return json.dumps({"error": f"No cash flow statement for {ticker}"})

    keys = [
        "Operating Cash Flow",
        "Free Cash Flow",
        "Investing Cash Flow",
        "Financing Cash Flow",
        "Capital Expenditure",
    ]
    key_rows = [row for row in cf.index if any(k in row for k in keys)]
    summary = _df_to_summary(cf.loc[cf.index.isin(key_rows)])
    return json.dumps({"ticker": ticker.upper(), "cash_flow": summary})


def get_key_ratios(ticker: str) -> str:
    """Get key valuation and profitability ratios (P/E, P/B, ROE, ROA, margins, debt/equity)."""
    t = yf.Ticker(ticker)
    try:
        info = t.info or {}
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)})

    if not info:
        return json.dumps({"error": f"No ratio data for {ticker}"})

    payload = {
        "ticker": ticker.upper(),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "price_to_book": info.get("priceToBook"),
        "peg_ratio": info.get("pegRatio") or info.get("trailingPegRatio"),
        "return_on_equity": info.get("returnOnEquity"),
        "return_on_assets": info.get("returnOnAssets"),
        "profit_margin": info.get("profitMargins"),
        "operating_margin": info.get("operatingMargins"),
        "debt_to_equity": info.get("debtToEquity"),
        "current_ratio": info.get("currentRatio"),
        "dividend_yield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
    }
    return json.dumps(payload)
