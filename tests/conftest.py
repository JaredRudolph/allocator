import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_prices() -> pd.DataFrame:
    np.random.seed(42)
    n = 600  # ~2.4 years of business days -- enough for the rolling optimization window
    dates = pd.date_range("2018-01-01", periods=n, freq="B")
    tickers = ["A", "B", "C"]
    data = {}
    for i, t in enumerate(tickers):
        daily_returns = np.random.normal(0.0003 * (i + 1), 0.012, n)
        data[t] = 100.0 * np.cumprod(1.0 + daily_returns)
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def base_config() -> dict:
    return {
        "tickers": ["A", "B", "C"],
        "benchmark": "A",
        "start": "2018-01-01",
        "end": None,
        "initial_capital": 10_000,
        "risk_free_rate": 0.0,
        "contribution": {
            "amount": 500,
            "frequency": "M",
            "method": "smart",
        },
        "rebalance": {
            "mode": "corridor",
            "threshold_type": "relative",
            "band": 0.10,
            "schedule": "Q",
        },
        "optimize": "equal_weight",
    }
