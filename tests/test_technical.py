import numpy as np
import pandas as pd

from financial_agent.tools.technical import _rsi, _sma


def test_sma_basic():
    series = pd.Series([1, 2, 3, 4, 5])
    result = _sma(series, window=2)
    assert np.isclose(result.iloc[-1], 4.5)


def test_rsi_strictly_increasing_series_hits_100():
    series = pd.Series(range(1, 30))  # monotonically increasing -> no losses
    result = _rsi(series, window=14)
    assert result.iloc[-1] == 100


def test_rsi_strictly_decreasing_series_hits_0():
    series = pd.Series(range(30, 1, -1))  # monotonically decreasing -> no gains
    result = _rsi(series, window=14)
    assert result.iloc[-1] == 0
