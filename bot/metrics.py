"""Performance metrics computed from an equity curve and trade list."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .portfolio import Trade

PERIODS_PER_YEAR_1H = 24 * 365


def total_return(equity: pd.Series) -> float:
    return float(equity.iloc[-1] / equity.iloc[0] - 1)


def sharpe_ratio(equity: pd.Series, periods_per_year: int = PERIODS_PER_YEAR_1H) -> float:
    rets = equity.pct_change().dropna()
    if rets.std() == 0 or len(rets) < 2:
        return 0.0
    return float(rets.mean() / rets.std() * np.sqrt(periods_per_year))


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min())


def round_trips(trades: list[Trade]) -> list[float]:
    """Pair BUY->SELL legs into round-trip P&L fractions (net of fees)."""
    trips: list[float] = []
    open_qty = 0.0
    open_cost = 0.0  # notional + fees paid on the way in
    for t in trades:
        if t.side == "BUY":
            open_qty += t.quantity
            open_cost += t.notional + t.fee
        else:  # SELL closes (FIFO not needed for long/flat: always all-in/all-out)
            if open_qty > 0:
                proceeds = t.notional - t.fee
                trips.append(proceeds / open_cost - 1)
                open_qty = 0.0
                open_cost = 0.0
    return trips


def win_rate(trades: list[Trade]) -> float:
    trips = round_trips(trades)
    if not trips:
        return 0.0
    return float(np.mean([p > 0 for p in trips]))


def buy_and_hold_return(df: pd.DataFrame) -> float:
    return float(df["close"].iloc[-1] / df["close"].iloc[0] - 1)
