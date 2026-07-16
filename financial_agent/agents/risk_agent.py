"""Risk Assessment agent: volatility, drawdown, beta, Sharpe ratio, VaR."""

from __future__ import annotations

from ..tools.risk import compute_risk_metrics
from .base import Agent

TOOLS = [
    {
        "name": "compute_risk_metrics",
        "description": (
            "Compute annualized volatility, max drawdown, Sharpe ratio, 95% daily VaR, and "
            "beta versus a benchmark index (default S&P 500) for a ticker."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "period": {
                    "type": "string",
                    "description": "History window to compute risk metrics over, e.g. 6mo, 1y, 3y",
                    "default": "1y",
                },
                "benchmark": {
                    "type": "string",
                    "description": "Benchmark ticker for beta calculation",
                    "default": "^GSPC",
                },
            },
            "required": ["ticker"],
        },
    },
]

TOOL_IMPLS = {"compute_risk_metrics": compute_risk_metrics}

SYSTEM_PROMPT = """You are the Risk Assessment agent in a multi-agent financial analysis system.

Use your tools to compute risk metrics for the requested ticker, then write a risk \
assessment covering:
- Volatility: how volatile the stock has been (annualized), in plain terms
- Drawdown: the worst peak-to-trough decline observed, and what that implies about downside risk
- Beta: how the stock moves relative to the broader market (more/less volatile than the market)
- Risk-adjusted return: what the Sharpe ratio says about return per unit of risk taken
- Value at Risk: the rough daily loss threshold at a 95% confidence level

Cite the actual numbers. Conclude with an overall risk tier (Low / Moderate / High / Very \
High) and a one-sentence justification. Do not give a buy/sell recommendation.
"""


def build_risk_agent() -> Agent:
    return Agent(
        name="risk",
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        tool_impls=TOOL_IMPLS,
        effort="medium",
        max_tokens=2048,
    )
