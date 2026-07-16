# Financial Agent Application

A multi-agent financial analysis system built on the Claude API. Five
specialist agents research a stock ticker in parallel, and a report-writer
agent synthesizes their findings into a single investment research report.

## Architecture

```
                        ┌────────────────────┐
                        │   Orchestrator      │
                        │ (FinancialAnalysis   │
                        │   Orchestrator)      │
                        └──────────┬───────────┘
                                   │ fan-out (asyncio.gather)
       ┌─────────────┬────────────┼────────────┬──────────────┐
       ▼             ▼            ▼             ▼              ▼
 ┌───────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐
 │Market Data│ │Fundamental│ │Technical │ │   Risk    │ │ Sentiment  │
 │  Agent    │ │  Agent    │ │  Agent   │ │  Agent    │ │   Agent    │
 └─────┬─────┘ └─────┬─────┘ └────┬─────┘ └─────┬─────┘ └─────┬──────┘
       │  yfinance    │  yfinance  │  yfinance   │  yfinance   │ web_search
       ▼             ▼            ▼             ▼             (server tool)
                                   │
                                   ▼
                       ┌────────────────────┐
                       │  Report Writer      │
                       │      Agent          │
                       └──────────┬──────────┘
                                  ▼
                         Final research report
```

Each specialist is a Claude agent scoped to one job, with its own system
prompt and its own tool set:

| Agent | Responsibility | Tools |
|---|---|---|
| **Market Data** | Current price, company profile, recent price history, analyst ratings | `get_stock_price`, `get_company_info`, `get_historical_prices`, `get_analyst_recommendations` |
| **Fundamental Analysis** | Revenue/earnings trends, profitability, balance sheet strength, valuation | `get_income_statement`, `get_balance_sheet`, `get_cash_flow`, `get_key_ratios` |
| **Technical Analysis** | Moving averages, RSI, MACD, short-term trend | `get_historical_prices`, `compute_technical_indicators` |
| **Risk Assessment** | Volatility, drawdown, beta, Sharpe ratio, Value at Risk | `compute_risk_metrics` |
| **News & Sentiment** | Recent headlines and market sentiment | Claude's server-side `web_search` tool |
| **Report Writer** | Synthesizes all of the above into one cohesive report | — |

Data-fetching tools are backed by [yfinance](https://github.com/ranaroussi/yfinance)
(free, no API key required). The agent loop itself is a manual Claude
tool-use loop (`financial_agent/claude_runner.py`) — each agent calls
`messages.create`, executes any requested client-side tools locally, and
feeds results back until Claude produces its final answer.

A failure in one specialist doesn't abort the run: the orchestrator catches
per-agent exceptions, records them as a gap in that agent's findings, and
still produces a report — the report writer is instructed to call out any
missing data explicitly rather than paper over it.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt          # runtime deps
pip install -r requirements-dev.txt      # + test deps

cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY (or run `ant auth login` instead)
export $(grep -v '^#' .env | xargs)      # or use python-dotenv / direnv
```

## Usage

### CLI

```bash
python main.py analyze AAPL
python main.py analyze AAPL --format json
```

### REST API

```bash
uvicorn financial_agent.api:app --reload
```

```bash
curl -X POST http://localhost:8000/analyze -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'

# or
curl http://localhost:8000/analyze/AAPL
curl http://localhost:8000/health
```

Interactive API docs are available at `http://localhost:8000/docs` once the
server is running.

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Claude API credentials (or use `ant auth login`) |
| `FINANCIAL_AGENT_MODEL` | `claude-opus-4-8` | Model used by every agent |
| `FINANCIAL_AGENT_MAX_ITERATIONS` | `8` | Max tool-use round trips per agent |

## Testing

```bash
pytest
```

Tests mock the Claude API and yfinance, so they run without network access
or API credentials. They cover the tool-use loop mechanics
(`test_claude_runner.py`), the technical/risk math (`test_technical.py`,
`test_risk.py`), and orchestrator fan-out/failure handling
(`test_orchestrator.py`).

## Disclaimer

This tool produces informational research summaries only. It is not
personalized financial advice, and the underlying data (Yahoo Finance via
yfinance) may be delayed or incomplete. Always verify figures against a
primary source before making investment decisions.
