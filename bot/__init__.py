"""Crypto trading bot sample: backtesting engine + paper trading.

Package layout:
    bot.data        load OHLCV candles from CSV
    bot.indicators  SMA / RSI implemented in numpy
    bot.strategy    Strategy interface (target-position signals)
    bot.strategies  SMA crossover + RSI mean-reversion
    bot.portfolio   cash/position accounting with fees + slippage
    bot.engine      the backtest loop (no lookahead: signals execute
                    at the *next* bar's open)
    bot.metrics     return, Sharpe, max drawdown, win rate
"""
from .strategy import Strategy
from .strategies import RSIMeanReversionStrategy, SMACrossoverStrategy
from .portfolio import Portfolio, Trade
from .engine import BacktestResult, run_backtest
from . import metrics

__all__ = [
    "Strategy",
    "SMACrossoverStrategy",
    "RSIMeanReversionStrategy",
    "Portfolio",
    "Trade",
    "BacktestResult",
    "run_backtest",
    "metrics",
]
