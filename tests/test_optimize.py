import numpy as np
import pytest

from allocator.optimize import optimize


def test_equal_weight(synthetic_prices):
    returns = synthetic_prices.pct_change().dropna()
    n = synthetic_prices.shape[1]
    weights = optimize(returns, "equal_weight")
    assert weights.shape == (n,)
    assert abs(weights.sum() - 1.0) < 1e-6
    assert all(abs(w - 1.0 / n) < 1e-6 for w in weights)


def test_max_sharpe_valid_weights(synthetic_prices):
    returns = synthetic_prices.pct_change().dropna()
    weights = optimize(returns, "max_sharpe")
    assert weights.shape == (synthetic_prices.shape[1],)
    assert abs(weights.sum() - 1.0) < 1e-6
    assert all(w >= -1e-6 for w in weights)


def test_min_vol_valid_weights(synthetic_prices):
    returns = synthetic_prices.pct_change().dropna()
    weights = optimize(returns, "min_vol")
    assert weights.shape == (synthetic_prices.shape[1],)
    assert abs(weights.sum() - 1.0) < 1e-6
    assert all(w >= -1e-6 for w in weights)


def test_unknown_objective_raises(synthetic_prices):
    returns = synthetic_prices.pct_change().dropna()
    with pytest.raises(ValueError, match="Unknown objective"):
        optimize(returns, "bad_objective")


def test_insufficient_history_falls_back_to_equal_weight(synthetic_prices):
    short_returns = synthetic_prices.pct_change().dropna().iloc[:10]
    n = synthetic_prices.shape[1]
    weights = optimize(short_returns, "max_sharpe")
    assert all(abs(w - 1.0 / n) < 1e-6 for w in weights)
