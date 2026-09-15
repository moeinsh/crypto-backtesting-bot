"""Strategy interface: strategies emit *target positions*, never orders.

A strategy looks at closed candles and returns, for every bar, the
desired position AFTER that bar: 1 = fully long, 0 = flat. The engine
decides when and how to trade (next-bar-open execution, fees, slippage),
so strategies stay pure signal logic and are reusable in both the
backtester and the paper-trading bot.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class Strategy(ABC):
    name: str = "base"
    warmup_bars: int = 0  # bars to skip before signals are valid

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Return target position (0 or 1) per bar, indexed like ``df``."""
        raise NotImplementedError

    def _zeros(self, df: pd.DataFrame) -> pd.Series:
        return pd.Series(np.zeros(len(df), dtype=int), index=df.index)
