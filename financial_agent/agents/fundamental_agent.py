"""Fundamental Analysis agent: financial statements and valuation ratios."""

from __future__ import annotations

from ..tools.financials import (
    get_balance_sheet,
    get_cash_flow,
    get_income_statement,
    get_key_ratios,
)
from .base import Agent

TOOLS = [
    {
        "name": "get_income_statement",
        "description": "Get recent annual income statement line items: revenue, gross profit, operating income, net income, EBITDA.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "get_balance_sheet",
        "description": "Get recent annual balance sheet line items: total assets, liabilities, equity, debt, cash.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "get_cash_flow",
        "description": "Get recent annual cash flow line items: operating, investing, financing cash flow, and free cash flow.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "get_key_ratios",
        "description": "Get key valuation and profitability ratios: P/E, P/B, PEG, ROE, ROA, margins, debt/equity, dividend yield.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
]

TOOL_IMPLS = {
    "get_income_statement": get_income_statement,
    "get_balance_sheet": get_balance_sheet,
    "get_cash_flow": get_cash_flow,
    "get_key_ratios": get_key_ratios,
}

SYSTEM_PROMPT = """You are the Fundamental Analysis agent in a multi-agent financial analysis system.

Use your tools to pull the income statement, balance sheet, cash flow statement, and key \
ratios for the requested ticker. Then write a fundamental analysis covering:
- Revenue and earnings trends (growth or decline, and by how much)
- Profitability (margins, ROE, ROA) relative to what's healthy for the company's likely sector
- Balance sheet strength (debt levels, liquidity, cash position)
- Valuation (is the P/E, P/B, PEG reasonable, expensive, or cheap, and versus what baseline)

Cite the actual numbers you retrieved. If a statement is unavailable, note the gap rather \
than inventing figures. Do not give a buy/sell recommendation — that synthesis happens \
downstream.
"""


def build_fundamental_agent() -> Agent:
    return Agent(
        name="fundamental",
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        tool_impls=TOOL_IMPLS,
        effort="medium",
        max_tokens=3072,
    )
