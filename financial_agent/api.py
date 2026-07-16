"""FastAPI wrapper exposing the multi-agent pipeline over HTTP.

Run with: uvicorn financial_agent.api:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .orchestrator import FinancialAnalysisOrchestrator

app = FastAPI(
    title="Financial Agent Application",
    description="Multi-agent financial analysis system powered by Claude.",
    version="0.1.0",
)

# Constructed lazily so importing this module (e.g. for tests, or OpenAPI
# generation) doesn't require ANTHROPIC_API_KEY to be set.
_orchestrator: FinancialAnalysisOrchestrator | None = None


def get_orchestrator() -> FinancialAnalysisOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = FinancialAnalysisOrchestrator()
    return _orchestrator


class AnalyzeRequest(BaseModel):
    ticker: str


class AnalyzeResponse(BaseModel):
    ticker: str
    generated_at: str
    report: str
    agent_findings: dict[str, str]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    ticker = request.ticker.strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="ticker is required")
    try:
        result = await get_orchestrator().analyze(ticker)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}") from exc
    return AnalyzeResponse(
        ticker=result.ticker,
        generated_at=result.generated_at,
        report=result.report,
        agent_findings=result.agent_findings,
    )


@app.get("/analyze/{ticker}", response_model=AnalyzeResponse)
async def analyze_get(ticker: str) -> AnalyzeResponse:
    return await analyze(AnalyzeRequest(ticker=ticker))
