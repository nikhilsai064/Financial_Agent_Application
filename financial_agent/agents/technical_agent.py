"""Technical Analysis agent: price trends and momentum indicators."""

from __future__ import annotations

from ..tools.market_data import get_historical_prices
from ..tools.technical import compute_technical_indicators
from .base import Agent

TOOLS = [
    {
        "name": "get_historical_prices",
        "description": "Get historical price summary statistics for a ticker over a period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "period": {"type": "string", "default": "6mo"},
                "interval": {"type": "string", "default": "1d"},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "compute_technical_indicators",
        "description": "Compute SMA20/SMA50, RSI14, MACD, and short-term trend from recent daily price history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "period": {
                    "type": "string",
                    "description": "History window to compute indicators over, e.g. 3mo, 6mo, 1y",
                    "default": "6mo",
                },
            },
            "required": ["ticker"],
        },
    },
]

TOOL_IMPLS = {
    "get_historical_prices": get_historical_prices,
    "compute_technical_indicators": compute_technical_indicators,
}

SYSTEM_PROMPT = """You are the Technical Analysis agent in a multi-agent financial analysis system.

Use your tools to pull recent price history and compute technical indicators (moving \
averages, RSI, MACD, trend) for the requested ticker. Then write a technical analysis \
covering:
- Where price sits relative to its 20-day and 50-day moving averages
- Momentum: is RSI signaling overbought (>70), oversold (<30), or neutral, and what does \
  MACD suggest about momentum direction
- The prevailing short-term trend and how strong/weak it looks

Cite the actual indicator values. This is a technical read only — do not blend in \
fundamentals or news, and do not give a buy/sell recommendation.
"""


def build_technical_agent() -> Agent:
    return Agent(
        name="technical",
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        tool_impls=TOOL_IMPLS,
        effort="medium",
        max_tokens=2048,
    )
