"""Market Data agent: current price, company profile, price history, analyst ratings."""

from __future__ import annotations

from ..tools.market_data import (
    get_analyst_recommendations,
    get_company_info,
    get_historical_prices,
    get_stock_price,
)
from .base import Agent

TOOLS = [
    {
        "name": "get_stock_price",
        "description": (
            "Get the latest price, day change, and volume for a stock ticker. "
            "Call this first for any request about a specific stock."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker symbol, e.g. AAPL"},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_company_info",
        "description": "Get company profile: sector, industry, market cap, business summary.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "get_historical_prices",
        "description": "Get historical price summary statistics for a ticker over a period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "period": {
                    "type": "string",
                    "description": "e.g. 1mo, 3mo, 6mo, 1y, 5y",
                    "default": "6mo",
                },
                "interval": {
                    "type": "string",
                    "description": "e.g. 1d, 1wk, 1mo",
                    "default": "1d",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_analyst_recommendations",
        "description": "Get recent Wall Street analyst recommendation ratings for a ticker.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
]

TOOL_IMPLS = {
    "get_stock_price": get_stock_price,
    "get_company_info": get_company_info,
    "get_historical_prices": get_historical_prices,
    "get_analyst_recommendations": get_analyst_recommendations,
}

SYSTEM_PROMPT = """You are the Market Data agent in a multi-agent financial analysis system.

Your job: gather the current price, company profile, recent price history, and analyst \
recommendations for the requested ticker using your tools, then write a concise, factual \
summary (bullet points) of what you found. Include exact numbers, percentages, and dates. \
Do not speculate, interpret, or give investment advice — that is other agents' job. If a \
tool returns an error, say so plainly instead of guessing at the data.
"""


def build_market_data_agent() -> Agent:
    return Agent(
        name="market_data",
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        tool_impls=TOOL_IMPLS,
        effort="low",
        max_tokens=2048,
    )
