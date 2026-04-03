from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class RebalanceEvent:
    date: pd.Timestamp
    trigger: str
    pre_weights: dict[str, float]
    post_weights: dict[str, float]


def check_corridor_breach(
    weights: np.ndarray,
    targets: np.ndarray,
    band: float,
    threshold_type: str,
) -> bool:
    """Return True if any weight falls outside its corridor band."""
    if threshold_type == "absolute":
        lower = targets - band
        upper = targets + band
    elif threshold_type == "relative":
        lower = targets * (1.0 - band)
        upper = targets * (1.0 + band)
    else:
        raise ValueError(f"Unknown threshold_type: {threshold_type!r}")

    return bool(np.any(weights < lower) or np.any(weights > upper))


def needs_rebalance(
    cfg: dict,
    date: pd.Timestamp,
    last_rebalance_date: pd.Timestamp,
    current_breach: bool,
    breach_since_last: bool,
) -> bool:
    """Determine whether a rebalance should execute on this date.

    cfg is the rebalance sub-config (cfg['rebalance']).
    breach_since_last should accumulate corridor breaches since the last rebalance;
    the caller is responsible for resetting it after each rebalance.
    """
    mode = cfg["mode"]

    if mode == "corridor":
        return current_breach
    elif mode == "periodic":
        return _is_scheduled(date, cfg.get("schedule", "Q"), last_rebalance_date)
    elif mode == "hybrid":
        on_schedule = _is_scheduled(date, cfg.get("schedule", "Q"), last_rebalance_date)
        return on_schedule and breach_since_last
    else:
        raise ValueError(f"Unknown rebalance mode: {mode!r}")


def _is_scheduled(
    date: pd.Timestamp,
    schedule: str,
    last_date: pd.Timestamp,
) -> bool:
    if schedule == "M":
        return date.month != last_date.month or date.year != last_date.year
    if schedule == "Q":
        return date.quarter != last_date.quarter or date.year != last_date.year
    raise ValueError(f"Unknown schedule: {schedule!r}")
