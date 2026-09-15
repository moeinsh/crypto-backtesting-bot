"""OHLCV data loading."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_candles(csv_path: str | Path) -> pd.DataFrame:
    """Load 1h (or any) klines CSV into a clean DataFrame.

    Expected columns: open_time, open, high, low, close, volume.
    open_time may be ISO-8601 or epoch milliseconds.
    Returns the frame sorted by time with a DatetimeIndex.
    """
    df = pd.read_csv(csv_path)
    df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"]).sort_values("open_time")
    return df.set_index("open_time")
