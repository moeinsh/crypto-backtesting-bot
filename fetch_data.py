"""Download real historical klines from the Binance PUBLIC API (no key needed).

GET /api/v3/klines is a public market-data endpoint. api.binance.com
geo-blocks some regions (HTTP 451), so we fall back to api.binance.us —
same endpoint, same schema.
"""
from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

BASES = ["https://api.binance.com", "https://api.binance.us"]
HEADERS = {"User-Agent": "crypto-trading-bot-sample/1.0"}


def pick_base() -> str:
    for base in BASES:
        try:
            r = requests.get(f"{base}/api/v3/ping", headers=HEADERS, timeout=10)
            if r.status_code == 200:
                return base
        except requests.RequestException:
            continue
    raise RuntimeError("No reachable Binance public API endpoint")


def fetch_klines(base: str, symbol: str, interval: str,
                 start_ms: int, end_ms: int) -> list:
    """Paginate klines (max 1000 per request) between two epoch-ms bounds."""
    out: list = []
    start = start_ms
    while start < end_ms:
        params = {"symbol": symbol, "interval": interval,
                  "startTime": start, "endTime": end_ms, "limit": 1000}
        r = requests.get(f"{base}/api/v3/klines", params=params,
                         headers=HEADERS, timeout=20)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        out.extend(batch)
        start = batch[-1][0] + 1  # continue after the last candle
        time.sleep(0.3)  # polite pacing
        if len(batch) < 1000:
            break
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch Binance klines to CSV")
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--interval", default="1h")
    ap.add_argument("--days", type=int, default=120,
                    help="how many days of history to fetch")
    ap.add_argument("--out", default="data/btcusdt_1h.csv")
    args = ap.parse_args()

    base = pick_base()
    print(f"Using public endpoint: {base}")
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.days)
    klines = fetch_klines(base, args.symbol, args.interval,
                          int(start.timestamp() * 1000),
                          int(end.timestamp() * 1000))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["open_time", "open", "high", "low", "close", "volume"])
        for k in klines:
            ts = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).isoformat()
            w.writerow([ts, k[1], k[2], k[3], k[4], k[5]])
    print(f"Wrote {len(klines)} {args.interval} candles "
          f"({args.symbol}) -> {out}")


if __name__ == "__main__":
    main()
