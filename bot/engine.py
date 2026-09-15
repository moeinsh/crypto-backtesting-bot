"""The backtest loop.

No-lookahead rule: a signal computed from bar *t* (closed data only) is
executed at the OPEN of bar *t+1*. Equity is marked to market at every
bar's close.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .portfolio import Portfolio, Trade
from .strategy import Strategy


@dataclass
class BacktestResult:
    strategy_name: str
    equity_curve: pd.Series          # equity per bar (USDT)
    trades: list[Trade] = field(default_factory=list)
    start_cash: float = 10_000.0


def run_backtest(df: pd.DataFrame, strategy: Strategy,
                 start_cash: float = 10_000.0) -> BacktestResult:
    signals = strategy.generate_signals(df)
    portfolio = Portfolio(cash=start_cash)
    equity = pd.Series(index=df.index, dtype=float)

    closes = df["close"].to_numpy()
    opens = df["open"].to_numpy()

    for i in range(len(df)):
        if i > 0:
            # Act on the previous bar's signal, at this bar's open.
            portfolio.set_position(df.index[i], float(opens[i]), int(signals.iloc[i - 1]))
        equity.iloc[i] = portfolio.equity(float(closes[i]))

    return BacktestResult(strategy.name, equity, portfolio.trades, start_cash)
