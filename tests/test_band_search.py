import numpy as np
import pandas as pd
import pytest

from corridor_backtest.band_search import search_band

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_prices(n_days=504, seed=7):
    rng = np.random.default_rng(seed)
    returns = rng.normal(loc=0.0003, scale=0.01, size=(n_days, 2))
    prices = np.cumprod(1 + returns, axis=0) * 100
    index = pd.date_range("2020-01-01", periods=n_days, freq="B")
    return pd.DataFrame(prices, index=index, columns=["SPY", "TLT"])


def _base_config(metric="sharpe", steps=5):
    return {
        "name": "test",
        "tickers": ["SPY", "TLT"],
        "weights": {"SPY": 0.60, "TLT": 0.40},
        "initial_capital": 10000,
        "contribution": None,
        "rebalance": {
            "mode": "corridor",
            "threshold_type": "absolute",
            "rebalance_to": "target",
            "band": 0.05,
            "schedule": "Q",
        },
        "band_search": {
            "metric": metric,
            "band_range": [0.02, 0.20],
            "steps": steps,
        },
    }


def _two_band_config(metric="calmar", steps=4):
    return {
        "name": "test_2d",
        "tickers": ["SPY", "TLT"],
        "weights": {"SPY": 0.60, "TLT": 0.40},
        "initial_capital": 10000,
        "contribution": None,
        "rebalance": {
            "mode": "corridor",
            "threshold_type": "absolute",
            "rebalance_to": "band_edge",
            "band": 0.03,
            "corridor": 0.10,
            "schedule": "Q",
        },
        "band_search": {
            "metric": metric,
            "band_range": [0.02, 0.06],
            "corridor_range": [0.08, 0.18],
            "steps": steps,
        },
    }


# ---------------------------------------------------------------------------
# 1D search -- return structure
# ---------------------------------------------------------------------------


def test_search_band_returns_tuple():
    prices = _make_prices()
    result = search_band(prices, _base_config())
    assert isinstance(result, tuple) and len(result) == 2


def test_search_band_best_params_is_dict():
    prices = _make_prices()
    best_params, _ = search_band(prices, _base_config())
    assert isinstance(best_params, dict)
    assert "band" in best_params


def test_search_band_best_params_value_is_float():
    prices = _make_prices()
    best_params, _ = search_band(prices, _base_config())
    assert isinstance(best_params["band"], float)


def test_search_band_results_columns():
    prices = _make_prices()
    _, results = search_band(prices, _base_config())
    assert set(results.columns) >= {"band", "metric", "score"}


def test_search_band_results_row_count_matches_steps():
    prices = _make_prices()
    steps = 35
    _, results = search_band(prices, _base_config(steps=steps))
    assert len(results) == steps


def test_search_band_results_sorted_descending():
    prices = _make_prices()
    _, results = search_band(prices, _base_config())
    scores = results["score"].values
    assert np.all(scores[:-1] >= scores[1:])


# ---------------------------------------------------------------------------
# 1D search -- best_params within range and consistent with top row
# ---------------------------------------------------------------------------


def test_search_band_best_params_within_range():
    prices = _make_prices()
    cfg = _base_config()
    lo, hi = cfg["band_search"]["band_range"]
    best_params, _ = search_band(prices, cfg)
    assert lo - 1e-9 <= best_params["band"] <= hi + 1e-9


def test_search_band_best_params_matches_top_row():
    prices = _make_prices()
    best_params, results = search_band(prices, _base_config())
    assert best_params["band"] == pytest.approx(results.iloc[0]["band"])


# ---------------------------------------------------------------------------
# 1D search -- corridor key is searched when present in rebalance config
# ---------------------------------------------------------------------------


def test_search_band_searches_corridor_when_two_band():
    prices = _make_prices()
    cfg = _base_config()
    cfg["rebalance"]["corridor"] = 0.12
    best_params, _ = search_band(prices, cfg)
    assert "corridor" in best_params
    assert "band" not in best_params


# ---------------------------------------------------------------------------
# 1D search -- all metrics run without error
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("metric", ["sharpe", "cagr", "calmar", "sortino"])
def test_search_band_all_metrics(metric):
    prices = _make_prices()
    best_params, results = search_band(prices, _base_config(metric=metric))
    assert np.isfinite(list(best_params.values())[0])
    assert results["metric"].iloc[0] == metric


# ---------------------------------------------------------------------------
# 2D search -- return structure
# ---------------------------------------------------------------------------


def test_search_band_2d_returns_tuple():
    prices = _make_prices()
    result = search_band(prices, _two_band_config())
    assert isinstance(result, tuple) and len(result) == 2


def test_search_band_2d_best_params_has_both_keys():
    prices = _make_prices()
    best_params, _ = search_band(prices, _two_band_config())
    assert "band" in best_params and "corridor" in best_params


def test_search_band_2d_results_has_corridor_column():
    prices = _make_prices()
    _, results = search_band(prices, _two_band_config())
    assert "corridor" in results.columns


def test_search_band_2d_corridor_always_greater_than_band():
    prices = _make_prices()
    _, results = search_band(prices, _two_band_config())
    assert (results["corridor"] > results["band"]).all()


def test_search_band_2d_best_params_within_range():
    prices = _make_prices()
    cfg = _two_band_config()
    band_lo, band_hi = cfg["band_search"]["band_range"]
    corr_lo, corr_hi = cfg["band_search"]["corridor_range"]
    best_params, _ = search_band(prices, cfg)
    assert band_lo - 1e-9 <= best_params["band"] <= band_hi + 1e-9
    assert corr_lo - 1e-9 <= best_params["corridor"] <= corr_hi + 1e-9


def test_search_band_2d_best_params_matches_top_row():
    prices = _make_prices()
    best_params, results = search_band(prices, _two_band_config())
    assert best_params["band"] == pytest.approx(results.iloc[0]["band"])
    assert best_params["corridor"] == pytest.approx(results.iloc[0]["corridor"])


def test_search_band_2d_results_sorted_descending():
    prices = _make_prices()
    _, results = search_band(prices, _two_band_config())
    scores = results["score"].values
    assert np.all(scores[:-1] >= scores[1:])


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_search_band_unknown_metric_raises():
    prices = _make_prices()
    cfg = _base_config()
    cfg["band_search"]["metric"] = "magic"
    with pytest.raises(ValueError, match="Unknown metric"):
        search_band(prices, cfg)


def test_search_band_missing_band_search_key_raises():
    prices = _make_prices()
    cfg = _base_config()
    del cfg["band_search"]
    with pytest.raises(KeyError):
        search_band(prices, cfg)
