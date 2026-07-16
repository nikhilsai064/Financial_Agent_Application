"""Coordinates the specialist agents into a single financial analysis report.

Flow:
  1. Five specialist agents run concurrently, each gathering and analyzing one
     slice of the picture (market data, fundamentals, technicals, risk, sentiment).
  2. Their findings are handed to a Report Writer agent, which synthesizes a
     single cohesive report.

A failure in any one specialist doesn't abort the run — it's recorded as a
gap and the report writer is told to call it out explicitly.
"""

from __future__ import annotations

import asyncio
import dataclasses
from datetime import datetime, timezone

import anthropic

from .agents.fundamental_agent import build_fundamental_agent
from .agents.market_data_agent import build_market_data_agent
from .agents.report_agent import build_report_agent
from .agents.risk_agent import build_risk_agent
from .agents.sentiment_agent import build_sentiment_agent
from .agents.technical_agent import build_technical_agent


@dataclasses.dataclass
class AnalysisReport:
    ticker: str
    generated_at: str
    report: str
    agent_findings: dict[str, str]


class FinancialAnalysisOrchestrator:
    """Coordinates specialist agents to produce a multi-agent financial analysis report."""

    def __init__(self, client: anthropic.AsyncAnthropic | None = None):
        self.client = client or anthropic.AsyncAnthropic()

    async def analyze(self, ticker: str) -> AnalysisReport:
        ticker = ticker.strip().upper()
        if not ticker:
            raise ValueError("ticker must not be empty")

        specialists = {
            "market_data": build_market_data_agent(),
            "fundamental": build_fundamental_agent(),
            "technical": build_technical_agent(),
            "risk": build_risk_agent(),
            "sentiment": build_sentiment_agent(),
        }
        prompts = {
            "market_data": f"Gather current market data for {ticker}.",
            "fundamental": (
                f"Perform a fundamental analysis of {ticker} using its financial "
                "statements and key ratios."
            ),
            "technical": (
                f"Perform a technical analysis of {ticker} using recent price history "
                "and momentum indicators."
            ),
            "risk": (
                f"Assess the risk profile of {ticker}: volatility, drawdown, beta, "
                "Sharpe ratio, and Value at Risk."
            ),
            "sentiment": f"Research recent news and market sentiment for {ticker}.",
        }

        keys = list(specialists.keys())
        results = await asyncio.gather(
            *(specialists[key].run(self.client, prompts[key]) for key in keys),
            return_exceptions=True,
        )

        findings: dict[str, str] = {}
        for key, result in zip(keys, results):
            if isinstance(result, BaseException):
                findings[key] = f"[Agent failed: {result}]"
            else:
                findings[key] = result.text or "[Agent returned no findings]"

        report_agent = build_report_agent()
        findings_block = "\n\n".join(
            f"## {key.replace('_', ' ').title()} Agent Findings\n{text}"
            for key, text in findings.items()
        )
        report_prompt = (
            f"Ticker: {ticker}\n\n"
            f"Here are the findings from the specialist agents:\n\n{findings_block}\n\n"
            "Write the final synthesized report now."
        )
        report_result = await report_agent.run(self.client, report_prompt)

        return AnalysisReport(
            ticker=ticker,
            generated_at=datetime.now(timezone.utc).isoformat(),
            report=report_result.text,
            agent_findings=findings,
        )
