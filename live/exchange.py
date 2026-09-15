"""Live-trading seam — DISABLED by default.

To go live you would:
  1. create API keys on your exchange (spot trading permission ONLY,
     withdrawals disabled, IP whitelist recommended),
  2. export BINANCE_API_KEY and BINANCE_API_SECRET,
  3. implement the three methods below against the exchange's
     private REST endpoints (or ccxt), and
  4. flip ``LIVE_TRADING_ENABLED`` to True.

Until then, importing or instantiating this class raises — paper
trading (paper_trade.py) is the only active mode.
"""
from __future__ import annotations

import os

LIVE_TRADING_ENABLED = os.getenv("LIVE_TRADING_ENABLED") == "1"


class LiveExchange:
    """Same shape as the paper loop expects: price + market orders."""

    def __init__(self) -> None:
        if not LIVE_TRADING_ENABLED:
            raise RuntimeError(
                "Live trading is DISABLED. Set LIVE_TRADING_ENABLED=1 and "
                "provide BINANCE_API_KEY / BINANCE_API_SECRET to enable it."
            )
        self.api_key = os.environ["BINANCE_API_KEY"]
        self.api_secret = os.environ["BINANCE_API_SECRET"]

    def get_price(self, symbol: str) -> float:  # pragma: no cover
        raise NotImplementedError("wire to GET /api/v3/ticker/price (signed)")

    def market_buy(self, symbol: str, quote_qty: float) -> dict:  # pragma: no cover
        raise NotImplementedError("wire to POST /api/v3/order (signed)")

    def market_sell(self, symbol: str, base_qty: float) -> dict:  # pragma: no cover
        raise NotImplementedError("wire to POST /api/v3/order (signed)")
