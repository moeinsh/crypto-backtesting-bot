"""Paper-trading bot: the SAME strategy interface, live public prices.

Each iteration:
  1. pulls the latest 1h klines + live ticker price from the Binance
     PUBLIC API (no key needed),
  2. computes the strategy's current target position,
  3. rebalances a PAPER portfolio (paper_state.json) toward it —
     no real orders are ever placed.

Run continuously with e.g.:
    python paper_trade.py --strategy rsi --interval 300
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from bot import RSIMeanReversionStrategy, SMACrossoverStrategy
from bot.data import load_candles
from bot.portfolio import Portfolio

ROOT = Path(__file__).resolve().parent
BASES = ["https://api.binance.com", "https://api.binance.us"]
HEADERS = {"User-Agent": "crypto-trading-bot-sample/1.0"}
STATE_FILE = ROOT / "paper_state.json"


def pick_base() -> str:
    for base in BASES:
        try:
            r = requests.get(f"{base}/api/v3/ping", headers=HEADERS, timeout=10)
            if r.status_code == 200:
                return base
        except requests.RequestException:
            continue
    raise RuntimeError("No reachable Binance public API endpoint")


def latest_klines(base: str, symbol: str, limit: int = 120) -> pd.DataFrame:
    r = requests.get(f"{base}/api/v3/klines",
                     params={"symbol": symbol, "interval": "1h", "limit": limit},
                     headers=HEADERS, timeout=20)
    r.raise_for_status()
    rows = [{
        "open_time": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).isoformat(),
        "open": k[1], "high": k[2], "low": k[3], "close": k[4], "volume": k[5],
    } for k in r.json()]
    tmp = ROOT / "data" / "_paper_tmp.csv"
    pd.DataFrame(rows).to_csv(tmp, index=False)
    try:
        return load_candles(tmp)
    finally:
        tmp.unlink(missing_ok=True)


def live_price(base: str, symbol: str) -> float:
    r = requests.get(f"{base}/api/v3/ticker/price",
                     params={"symbol": symbol}, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return float(r.json()["price"])


def load_state() -> Portfolio:
    if STATE_FILE.exists():
        s = json.loads(STATE_FILE.read_text())
        return Portfolio(cash=s["cash"], btc=s["btc"])
    return Portfolio(cash=10_000.0)


def save_state(p: Portfolio) -> None:
    STATE_FILE.write_text(json.dumps(
        {"cash": round(p.cash, 2), "btc": p.btc,
         "updated": datetime.now(timezone.utc).isoformat()}, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description="Paper-trade a strategy on live prices")
    ap.add_argument("--strategy", choices=["sma", "rsi"], default="rsi")
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--iterations", type=int, default=3,
                    help="how many check cycles to run")
    ap.add_argument("--interval", type=int, default=10,
                    help="seconds between cycles")
    args = ap.parse_args()

    strategy = SMACrossoverStrategy(20, 50) if args.strategy == "sma" \
        else RSIMeanReversionStrategy(14, 30, 70)
    base = pick_base()
    print(f"[paper] endpoint={base} strategy={strategy.name} "
          f"(NO real orders — paper portfolio only)")

    for i in range(args.iterations):
        df = latest_klines(base, args.symbol)
        price = live_price(base, args.symbol)
        target = int(strategy.generate_signals(df).iloc[-1])
        portfolio = load_state()
        now = pd.Timestamp.now(tz="UTC")
        trade = portfolio.set_position(now, price, target)
        save_state(portfolio)
        eq = portfolio.equity(price)
        pos = "LONG" if portfolio.position(price) else "FLAT"
        if trade:
            print(f"[paper] {now:%H:%M:%S} {trade.side} {trade.quantity:.6f} BTC "
                  f"@ ${trade.price:,.2f} | position={pos} equity=${eq:,.2f}")
        else:
            print(f"[paper] {now:%H:%M:%S} no action (target={target}) | "
                  f"position={pos} BTC={price:,.2f} equity=${eq:,.2f}")
        if i < args.iterations - 1:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
