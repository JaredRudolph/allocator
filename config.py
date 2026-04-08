portfolios = [
    {
        "name": "corridor_relative",
        "tickers": ["SPY", "TLT", "GLD", "QQQ"],
        "weights": {"SPY": 0.40, "TLT": 0.30, "GLD": 0.15, "QQQ": 0.15},
        "benchmark": "SPY",
        "start": "2015-01-01",
        "end": None,  # None defaults to today
        "initial_capital": 10_000,
        "risk_free_rate": 0.0,
        "contribution": {
            "amount": 500,
            "frequency": "M",  # M | Q | None
            "method": "smart",  # smart | pro_rata
        },
        "rebalance": {
            "mode": "corridor",  # none | periodic | corridor | hybrid
            "threshold_type": "relative",  # absolute | relative
            "band": 0.10,
            "rebalance_to": "target",  # target | band_edge
            "schedule": "Q",  # used if mode is periodic or hybrid
        },
        "optimize": {  # omit this key entirely to use fixed weights
            "objective": "max_sharpe",  # max_sharpe | min_vol | equal_weight
            "weight_bounds": {  # per-asset bounds
                "SPY": [0.10, 0.60],
                "TLT": [0.05, 0.45],
                "GLD": [0.05, 0.30],
                "QQQ": [0.05, 0.30],
            },
            # lazy global alternative:
            #   multipliers on initial weights, scales with allocation:
            # "weight_bounds": {"min": 0.25, "max": 1.75},
        },
        "band_search": {  # omit this key to skip parameter search
            "metric": "sharpe",  # sharpe | cagr | calmar | sortino
            "band_range": [0.02, 0.25],
            "steps": 20,
        },
    },
    {
        "name": "periodic_minvol",
        "tickers": ["SPY", "TLT", "GLD", "QQQ"],
        "weights": {"SPY": 0.40, "TLT": 0.30, "GLD": 0.15, "QQQ": 0.15},
        "benchmark": "SPY",
        "start": "2015-01-01",
        "end": None,
        "initial_capital": 10_000,
        "risk_free_rate": 0.0,
        "contribution": {
            "amount": 500,
            "frequency": "M",
            "method": "smart",
        },
        "rebalance": {
            "mode": "periodic",
            "threshold_type": "relative",
            "band": 0.10,
            "rebalance_to": "target",
            "schedule": "Q",
        },
        "optimize": {
            "objective": "min_vol",
            "weight_bounds": {
                "SPY": [0.10, 0.60],
                "TLT": [0.05, 0.45],
                "GLD": [0.05, 0.30],
                "QQQ": [0.05, 0.30],
            },
        },
    },
    {
        "name": "buy_and_hold",
        "tickers": ["SPY", "TLT", "GLD", "QQQ"],
        "weights": {"SPY": 0.40, "TLT": 0.30, "GLD": 0.15, "QQQ": 0.15},
        "benchmark": "SPY",
        "start": "2015-01-01",
        "end": None,
        "initial_capital": 10_000,
        "risk_free_rate": 0.0,
        "contribution": {
            "amount": 500,
            "frequency": "M",
            "method": "pro_rata",  # no targets to chase, split by initial weights
        },
        "rebalance": {
            "mode": "none",
            "threshold_type": "relative",
            "band": 0.10,
            "rebalance_to": "target",
            "schedule": "Q",
        },
    },
    # --- Popular and modern portfolios ---
    {
        # Ray Dalio's All Weather: designed to perform across all economic regimes.
        # Heavy bond allocation provides balance against equity drawdowns.
        "name": "all_weather",
        "tickers": ["SPY", "TLT", "IEF", "GLD", "DBC"],
        "weights": {"SPY": 0.30, "TLT": 0.40, "IEF": 0.15, "GLD": 0.075, "DBC": 0.075},
        "benchmark": "SPY",
        "start": "2015-01-01",
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
            "threshold_type": "absolute",
            "band": 0.05,
            "rebalance_to": "target",
            "schedule": "Q",
        },
    },
    {
        # Classic 60/40: the institutional benchmark for balanced portfolios.
        # Simple, low-cost, and historically effective over long horizons.
        "name": "sixty_forty",
        "tickers": ["SPY", "AGG"],
        "weights": {"SPY": 0.60, "AGG": 0.40},
        "benchmark": "SPY",
        "start": "2015-01-01",
        "end": None,
        "initial_capital": 10_000,
        "risk_free_rate": 0.0,
        "contribution": {
            "amount": 500,
            "frequency": "M",
            "method": "smart",
        },
        "rebalance": {
            "mode": "periodic",
            "threshold_type": "absolute",
            "band": 0.05,
            "rebalance_to": "target",
            "schedule": "Q",
        },
    },
    {
        # Golden Butterfly: equal-weighted across five asset classes covering
        # growth, value, bonds (long + short), and gold. Rebalances to band edge
        # to minimize turnover while controlling drift.
        "name": "golden_butterfly",
        "tickers": ["SPY", "IWN", "TLT", "SHY", "GLD"],
        "weights": {"SPY": 0.20, "IWN": 0.20, "TLT": 0.20, "SHY": 0.20, "GLD": 0.20},
        "benchmark": "SPY",
        "start": "2015-01-01",
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
            "threshold_type": "absolute",
            "band": 0.05,
            "rebalance_to": "band_edge",
            "schedule": "Q",
        },
    },
    {
        # Permanent Portfolio (Harry Browne): equal allocation across four regimes --
        # prosperity (stocks), inflation (gold), deflation (bonds), recession (cash).
        # Hybrid mode: only rebalances on schedule if drift has occurred.
        "name": "permanent_portfolio",
        "tickers": ["SPY", "TLT", "GLD", "BIL"],
        "weights": {"SPY": 0.25, "TLT": 0.25, "GLD": 0.25, "BIL": 0.25},
        "benchmark": "SPY",
        "start": "2015-01-01",
        "end": None,
        "initial_capital": 10_000,
        "risk_free_rate": 0.0,
        "contribution": {
            "amount": 500,
            "frequency": "M",
            "method": "smart",
        },
        "rebalance": {
            "mode": "hybrid",
            "threshold_type": "absolute",
            "band": 0.10,
            "rebalance_to": "target",
            "schedule": "Q",
        },
    },
    {
        # Global Growth: diversified across US large cap, US tech, international
        # developed, emerging markets, and long bonds. Max Sharpe optimizer with
        # band search finds the drift threshold that best balances return and risk.
        "name": "global_growth",
        "tickers": ["SPY", "QQQ", "EFA", "EEM", "TLT"],
        "weights": {"SPY": 0.35, "QQQ": 0.20, "EFA": 0.20, "EEM": 0.10, "TLT": 0.15},
        "benchmark": "SPY",
        "start": "2015-01-01",
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
            "rebalance_to": "target",
            "schedule": "Q",
        },
        "optimize": {
            "objective": "max_sharpe",
            "weight_bounds": {
                "SPY": [0.15, 0.55],
                "QQQ": [0.05, 0.40],
                "EFA": [0.05, 0.35],
                "EEM": [0.02, 0.25],
                "TLT": [0.05, 0.30],
            },
        },
        "band_search": {
            "metric": "calmar",
            "band_range": [0.02, 0.25],
            "steps": 20,
        },
    },
]
