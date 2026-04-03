import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROLLING_WINDOW_DAYS = 504  # 2 years of trading days
_MIN_HISTORY = 30


def optimize(returns: pd.DataFrame, objective: str) -> np.ndarray:
    """Return portfolio weights for the given objective.

    Uses the most recent ROLLING_WINDOW_DAYS of returns. Falls back to equal
    weight if history is insufficient or objective is 'equal_weight'.
    """
    n = returns.shape[1]
    equal = np.full(n, 1.0 / n)

    if objective == "equal_weight" or len(returns) < _MIN_HISTORY:
        return equal

    window = returns.iloc[-ROLLING_WINDOW_DAYS:]
    mu = window.mean() * 252
    cov = window.cov() * 252

    x0 = equal.copy()
    bounds = [(0.0, 1.0)] * n
    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]

    if objective == "max_sharpe":
        def objective_fn(w: np.ndarray) -> float:
            ret = float(w @ mu)
            vol = float(np.sqrt(w @ cov @ w))
            return -ret / vol if vol > 1e-12 else 0.0

    elif objective == "min_vol":
        def objective_fn(w: np.ndarray) -> float:
            return float(np.sqrt(w @ cov @ w))

    else:
        raise ValueError(f"Unknown objective: {objective!r}")

    result = minimize(
        objective_fn, x0, method="SLSQP", bounds=bounds, constraints=constraints
    )
    weights = np.clip(result.x, 0.0, 1.0)
    return weights / weights.sum()
