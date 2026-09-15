"""Technical indicators implemented in numpy (no TA-Lib dependency)."""
from __future__ import annotations

import numpy as np


def sma(values: np.ndarray, period: int) -> np.ndarray:
    """Simple moving average; first ``period - 1`` values are NaN (warmup)."""
    values = np.asarray(values, dtype=float)
    out = np.full_like(values, np.nan, dtype=float)
    if len(values) >= period:
        kernel = np.ones(period) / period
        out[period - 1 :] = np.convolve(values, kernel, mode="valid")
    return out


def rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
    """Wilder's RSI; first ``period`` values are NaN (warmup)."""
    closes = np.asarray(closes, dtype=float)
    out = np.full_like(closes, np.nan, dtype=float)
    if len(closes) <= period:
        return out
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = gains[:period].mean()
    avg_loss = losses[:period].mean()
    # Wilder smoothing from the first full window onward
    for i in range(period, len(closes)):
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else np.inf
        out[i] = 100.0 - 100.0 / (1.0 + rs)
    return out
