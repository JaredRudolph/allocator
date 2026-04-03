import numpy as np
import pandas as pd
import pytest

from allocator.rebalance import check_corridor_breach, needs_rebalance


def _ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s)


# -- check_corridor_breach --

def test_absolute_no_breach():
    targets = np.array([0.25, 0.375, 0.375])
    weights = np.array([0.25, 0.375, 0.375])
    assert not check_corridor_breach(weights, targets, band=0.05, threshold_type="absolute")


def test_absolute_breach_upper():
    targets = np.array([0.25, 0.375, 0.375])
    # weight[0] = 0.31 > 0.25 + 0.05 = 0.30
    weights = np.array([0.31, 0.345, 0.345])
    assert check_corridor_breach(weights, targets, band=0.05, threshold_type="absolute")


def test_absolute_breach_lower():
    targets = np.array([0.25, 0.375, 0.375])
    weights = np.array([0.19, 0.405, 0.405])
    assert check_corridor_breach(weights, targets, band=0.05, threshold_type="absolute")


def test_relative_no_breach():
    targets = np.array([0.25, 0.375, 0.375])
    # 10% relative: bounds for 0.25 are [0.225, 0.275]
    weights = np.array([0.26, 0.37, 0.37])
    assert not check_corridor_breach(weights, targets, band=0.10, threshold_type="relative")


def test_relative_breach():
    targets = np.array([0.25, 0.375, 0.375])
    # 0.22 < 0.25 * 0.90 = 0.225
    weights = np.array([0.22, 0.39, 0.39])
    assert check_corridor_breach(weights, targets, band=0.10, threshold_type="relative")


def test_unknown_threshold_type_raises():
    with pytest.raises(ValueError):
        check_corridor_breach(np.array([0.5, 0.5]), np.array([0.5, 0.5]), 0.1, "bad")


# -- needs_rebalance --

def test_corridor_triggers_on_breach():
    cfg = {"mode": "corridor", "band": 0.05, "threshold_type": "absolute", "schedule": "Q"}
    assert needs_rebalance(cfg, _ts("2020-04-01"), _ts("2020-01-01"), True, True)
    assert not needs_rebalance(cfg, _ts("2020-04-01"), _ts("2020-01-01"), False, False)


def test_periodic_triggers_on_schedule():
    cfg = {"mode": "periodic", "band": 0.05, "threshold_type": "absolute", "schedule": "Q"}
    # Q1 to Q2 -- different quarter, should rebalance
    assert needs_rebalance(cfg, _ts("2020-04-01"), _ts("2020-01-15"), False, False)
    # Both in Q1 -- no rebalance
    assert not needs_rebalance(cfg, _ts("2020-02-01"), _ts("2020-01-15"), False, False)


def test_hybrid_requires_schedule_and_breach():
    cfg = {"mode": "hybrid", "band": 0.05, "threshold_type": "absolute", "schedule": "Q"}
    # On schedule, no accumulated breach
    assert not needs_rebalance(cfg, _ts("2020-04-01"), _ts("2020-01-15"), False, False)
    # On schedule, breach accumulated
    assert needs_rebalance(cfg, _ts("2020-04-01"), _ts("2020-01-15"), False, True)
    # Off schedule, breach accumulated
    assert not needs_rebalance(cfg, _ts("2020-02-01"), _ts("2020-01-15"), False, True)


def test_unknown_mode_raises():
    cfg = {"mode": "bad", "band": 0.05, "threshold_type": "absolute", "schedule": "Q"}
    with pytest.raises(ValueError):
        needs_rebalance(cfg, _ts("2020-04-01"), _ts("2020-01-15"), False, False)
