import numpy as np
import pandas as pd
from loguru import logger

from .optimize import ROLLING_WINDOW_DAYS, optimize
from .rebalance import RebalanceEvent, check_corridor_breach, needs_rebalance


def run_backtest(
    prices: pd.DataFrame,
    cfg: dict,
) -> tuple[pd.DataFrame, list[RebalanceEvent]]:
    """Run the portfolio backtest over historical prices.

    Raises KeyError if any configured ticker is absent from prices.
    Returns a date-indexed results DataFrame and a list of rebalance events.
    """
    tickers: list[str] = cfg["tickers"]
    missing = [t for t in tickers if t not in prices.columns]
    if missing:
        raise KeyError(f"Missing tickers in price data: {missing}")

    prices = prices[tickers].copy()
    returns = prices.pct_change().dropna()

    rebal_cfg = cfg["rebalance"]
    contrib_cfg = cfg["contribution"]
    initial_capital: float = cfg["initial_capital"]
    n = len(tickers)

    targets = np.full(n, 1.0 / n)
    holdings: dict[str, float] = {
        t: targets[i] * initial_capital / float(prices.iloc[0][t])
        for i, t in enumerate(tickers)
    }

    records: list[dict] = []
    events: list[RebalanceEvent] = []
    # Initialize to first date so periodic/hybrid modes trigger at the first
    # scheduled boundary rather than never (None would make _is_scheduled return False).
    last_rebalance_date: pd.Timestamp = prices.index[0]
    last_contrib_date: pd.Timestamp = prices.index[0]
    breach_since_last = False

    for idx, date in enumerate(prices.index):
        price_row = prices.loc[date]
        port_value = sum(holdings[t] * float(price_row[t]) for t in tickers)
        weights = np.array(
            [holdings[t] * float(price_row[t]) / port_value for t in tickers]
        )

        # Apply contribution (skip first day -- initial capital is the first investment)
        contributed = 0.0
        freq = contrib_cfg.get("frequency")
        if idx > 0 and freq and _should_contribute(date, freq, last_contrib_date):
            holdings = _apply_contribution(
                holdings,
                price_row,
                weights,
                targets,
                contrib_cfg["amount"],
                contrib_cfg["method"],
                tickers,
            )
            last_contrib_date = date
            contributed = contrib_cfg["amount"]
            port_value = sum(holdings[t] * float(price_row[t]) for t in tickers)
            weights = np.array(
                [holdings[t] * float(price_row[t]) / port_value for t in tickers]
            )

        # Track corridor breaches (used by corridor and hybrid modes)
        current_breach = check_corridor_breach(
            weights, targets, rebal_cfg["band"], rebal_cfg["threshold_type"]
        )
        breach_since_last = breach_since_last or current_breach

        should_rebalance = needs_rebalance(
            rebal_cfg, date, last_rebalance_date, current_breach, breach_since_last
        )

        if should_rebalance:
            hist_returns = returns.loc[:date].iloc[-ROLLING_WINDOW_DAYS:]
            new_targets = optimize(hist_returns, cfg["optimize"])

            pre_weights = dict(zip(tickers, weights.tolist()))
            for i, t in enumerate(tickers):
                holdings[t] = new_targets[i] * port_value / float(price_row[t])

            targets = new_targets
            post_weights_arr = np.array(
                [holdings[t] * float(price_row[t]) / port_value for t in tickers]
            )
            events.append(
                RebalanceEvent(
                    date=date,
                    trigger=rebal_cfg["mode"],
                    pre_weights=pre_weights,
                    post_weights=dict(zip(tickers, post_weights_arr.tolist())),
                )
            )
            last_rebalance_date = date
            breach_since_last = False
            weights = post_weights_arr
            logger.debug(f"Rebalanced on {date.date()} ({len(events)} total)")

        records.append(
            {
                "date": date,
                "portfolio_value": port_value,
                **{f"weight_{t}": float(weights[i]) for i, t in enumerate(tickers)},
                "rebalanced": bool(should_rebalance),
                "contribution": contributed,
            }
        )

    results = pd.DataFrame(records).set_index("date")
    logger.info(
        f"Backtest complete: {len(prices)} days, {len(events)} rebalance events"
    )
    return results, events


def _should_contribute(
    date: pd.Timestamp, freq: str, last_date: pd.Timestamp
) -> bool:
    if freq == "M":
        return date.month != last_date.month or date.year != last_date.year
    if freq == "Q":
        return date.quarter != last_date.quarter or date.year != last_date.year
    raise ValueError(f"Unknown contribution frequency: {freq!r}")


def _apply_contribution(
    holdings: dict[str, float],
    price_row: pd.Series,
    weights: np.ndarray,
    targets: np.ndarray,
    amount: float,
    method: str,
    tickers: list[str],
) -> dict[str, float]:
    holdings = holdings.copy()
    if method == "smart":
        # Direct the full contribution to the most underweight asset
        deficits = targets - weights
        most_under = tickers[int(np.argmax(deficits))]
        holdings[most_under] += amount / float(price_row[most_under])
    elif method == "pro_rata":
        for i, t in enumerate(tickers):
            holdings[t] += (amount * targets[i]) / float(price_row[t])
    else:
        raise ValueError(f"Unknown contribution method: {method!r}")
    return holdings
