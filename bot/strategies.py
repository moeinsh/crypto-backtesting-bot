"""Two example strategies implementing the Strategy interface."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .indicators import rsi, sma
from .strategy import Strategy


class SMACrossoverStrategy(Strategy):
    """Trend following: long when the fast SMA is above the slow SMA.

    Classic momentum logic — rides sustained moves, whipsaws in
    sideways markets. Long/flat only, no leverage, no shorting.
    """

    name = "sma_crossover"

    def __init__(self, fast: int = 20, slow: int = 50):
        if fast >= slow:
            raise ValueError("fast must be < slow")
        self.fast = fast
        self.slow = slow
        self.warmup_bars = slow + 1

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].to_numpy()
        fast_ma = sma(close, self.fast)
        slow_ma = sma(close, self.slow)
        sig = self._zeros(df)
        sig[(fast_ma > slow_ma)] = 1
        sig.iloc[: self.warmup_bars] = 0  # no signals during indicator warmup
        return sig


class RSIMeanReversionStrategy(Strategy):
    """Mean reversion: buy dips (RSI < oversold), exit on strength.

    Buys when the 14-period RSI drops below ``oversold`` (weakness),
    goes flat when RSI rises above ``overbought`` (strength), and holds
    otherwise. Long/flat only, no leverage, no shorting.
    """

    name = "rsi_mean_reversion"

    def __init__(self, period: int = 14, oversold: float = 30.0, overbought: float = 70.0):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.warmup_bars = period + 1

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        r = rsi(df["close"].to_numpy(), self.period)
        sig = self._zeros(df)
        position = 0
        for i in range(len(df)):
            if i < self.warmup_bars or np.isnan(r[i]):
                sig.iloc[i] = 0
                position = 0
                continue
            if r[i] < self.oversold:
                position = 1
            elif r[i] > self.overbought:
                position = 0
            sig.iloc[i] = position
        return sig
