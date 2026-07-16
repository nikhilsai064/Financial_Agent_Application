from unittest.mock import AsyncMock

import pytest

from financial_agent.agents.base import Agent
from financial_agent.claude_runner import AgentResult
from financial_agent.orchestrator import FinancialAnalysisOrchestrator

EXPECTED_SPECIALISTS = {"market_data", "fundamental", "technical", "risk", "sentiment"}


@pytest.mark.asyncio
async def test_orchestrator_runs_specialists_and_synthesizes_report(monkeypatch):
    async def fake_run(self: Agent, client, user_prompt: str) -> AgentResult:
        return AgentResult(
            name=self.name,
            text=f"[{self.name}] findings for: {user_prompt[:30]}",
            raw_messages=[],
            stop_reason="end_turn",
        )

    monkeypatch.setattr(Agent, "run", fake_run)

    orchestrator = FinancialAnalysisOrchestrator(client=AsyncMock())
    report = await orchestrator.analyze("aapl")

    assert report.ticker == "AAPL"
    assert set(report.agent_findings.keys()) == EXPECTED_SPECIALISTS
    for key in EXPECTED_SPECIALISTS:
        assert report.agent_findings[key].startswith(f"[{key}]")

    # The report writer's output is not one of the specialist findings, it's the final report.
    assert report.report.startswith("[report_writer]")


@pytest.mark.asyncio
async def test_orchestrator_survives_a_failing_specialist(monkeypatch):
    async def fake_run(self: Agent, client, user_prompt: str) -> AgentResult:
        if self.name == "risk":
            raise RuntimeError("yfinance timeout")
        return AgentResult(name=self.name, text=f"[{self.name}] ok", raw_messages=[], stop_reason="end_turn")

    monkeypatch.setattr(Agent, "run", fake_run)

    orchestrator = FinancialAnalysisOrchestrator(client=AsyncMock())
    report = await orchestrator.analyze("MSFT")

    assert "Agent failed" in report.agent_findings["risk"]
    # A single failing specialist should not prevent the other findings or the final report.
    assert report.agent_findings["market_data"] == "[market_data] ok"
    assert report.report  # report writer still ran on the partial findings


@pytest.mark.asyncio
async def test_orchestrator_rejects_empty_ticker():
    orchestrator = FinancialAnalysisOrchestrator(client=AsyncMock())
    with pytest.raises(ValueError):
        await orchestrator.analyze("   ")
