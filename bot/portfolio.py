"""Paper portfolio accounting: cash + BTC position, fees, slippage."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Trade:
    timestamp: pd.Timestamp
    side: str          # "BUY" or "SELL"
    price: float       # filled price (after slippage)
    quantity: float    # BTC
    notional: float    # USDT value
    fee: float         # USDT


@dataclass
class Portfolio:
    cash: float = 10_000.0
    btc: float = 0.0
    fee_rate: float = 0.001        # 0.10% taker fee per side (Binance spot)
    slippage_rate: float = 0.0005  # 0.05% adverse move per side
    min_notional: float = 10.0     # ignore dust rebalances under $10
    trades: list = field(default_factory=list)

    def equity(self, price: float) -> float:
        return self.cash + self.btc * price

    def position(self, price: float) -> int:
        """Current position as 0/1: long if BTC value >= $10, else flat."""
        return 1 if self.btc * price >= self.min_notional else 0

    def set_position(self, timestamp: pd.Timestamp, price: float, target: int) -> Trade | None:
        """Rebalance toward ``target`` (0 = flat, 1 = fully long).

        Buys/sells the full difference at a slippage-adjusted fill price
        and deducts the taker fee from cash. Returns the Trade or None.
        """
        equity = self.equity(price)
        desired_btc = (equity / price) if target == 1 else 0.0
        delta = desired_btc - self.btc
        notional = abs(delta) * price
        if notional < self.min_notional:
            return None

        side = "BUY" if delta > 0 else "SELL"
        # Slippage moves the fill against us.
        fill = price * (1 + self.slippage_rate) if side == "BUY" else price * (1 - self.slippage_rate)
        fee = notional * self.fee_rate

        if side == "BUY":
            cost = notional + fee
            if cost > self.cash:  # never go negative; buy what we can afford
                notional = self.cash / (1 + self.fee_rate)
                delta = notional / price
                fee = notional * self.fee_rate
                cost = notional + fee
            self.cash -= cost
            self.btc += delta
        else:
            delta = -min(abs(delta), self.btc)
            notional = abs(delta) * price
            fee = notional * self.fee_rate
            self.btc += delta  # delta is negative
            self.cash += notional - fee

        trade = Trade(timestamp, side, round(fill, 2), round(abs(delta), 6),
                      round(notional, 2), round(fee, 2))
        self.trades.append(trade)
        return trade
