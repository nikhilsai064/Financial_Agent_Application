import json
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from financial_agent.tools.risk import compute_risk_metrics


def _fake_history(n: int = 260, start_price: float = 100.0, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    daily_returns = rng.normal(0.0005, 0.01, n)
    prices = start_price * (1 + daily_returns).cumprod()
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {
            "Close": prices,
            "High": prices * 1.01,
            "Low": prices * 0.99,
            "Volume": 1_000_000,
        },
        index=idx,
    )


def test_compute_risk_metrics_returns_expected_fields():
    fake_hist = _fake_history()

    def fake_ticker(symbol):
        mock = MagicMock()
        mock.history.return_value = fake_hist
        return mock

    with patch("financial_agent.tools.risk.yf.Ticker", side_effect=fake_ticker):
        result = json.loads(compute_risk_metrics("TEST", period="1y"))

    assert result["ticker"] == "TEST"
    assert "error" not in result
    for field in (
        "annualized_volatility_percent",
        "annualized_return_percent",
        "max_drawdown_percent",
        "sharpe_ratio",
        "value_at_risk_95_daily_percent",
        "beta_vs_benchmark",
    ):
        assert field in result

    # Volatility and drawdown should be sane for the simulated series.
    assert result["annualized_volatility_percent"] > 0
    assert result["max_drawdown_percent"] <= 0


def test_compute_risk_metrics_reports_error_on_insufficient_data():
    short_hist = _fake_history(n=5)

    def fake_ticker(symbol):
        mock = MagicMock()
        mock.history.return_value = short_hist
        return mock

    with patch("financial_agent.tools.risk.yf.Ticker", side_effect=fake_ticker):
        result = json.loads(compute_risk_metrics("TEST"))

    assert "error" in result
