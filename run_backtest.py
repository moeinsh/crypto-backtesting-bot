"""Run both strategies on real BTC/USDT data and write the report.

Outputs:
    backtest_report.txt  full metrics + every trade
    equity_curve.csv     timestamp, BTC close, equity per strategy
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from bot import RSIMeanReversionStrategy, SMACrossoverStrategy, metrics, run_backtest
from bot.data import load_candles

ROOT = Path(__file__).resolve().parent
START_CASH = 10_000.0


def summarize(name: str, result, df: pd.DataFrame) -> str:
    eq = result.equity_curve
    trips = metrics.round_trips(result.trades)
    n = len(trips)
    avg_trip = (sum(trips) / n * 100) if n else 0.0
    buys = sum(1 for t in result.trades if t.side == "BUY")
    sells = sum(1 for t in result.trades if t.side == "SELL")
    lines = [
        f"Strategy: {name}",
        f"  Period            : {df.index[0]} -> {df.index[-1]} ({len(df)} 1h candles)",
        f"  Start equity      : ${START_CASH:,.2f}",
        f"  End equity        : ${eq.iloc[-1]:,.2f}",
        f"  Total return      : {metrics.total_return(eq) * 100:+.2f}%",
        f"  Buy & hold return : {metrics.buy_and_hold_return(df) * 100:+.2f}%",
        f"  Sharpe (ann.)     : {metrics.sharpe_ratio(eq):+.2f}",
        f"  Max drawdown      : {metrics.max_drawdown(eq) * 100:.2f}%",
        f"  Trades            : {len(result.trades)} ({buys} buys / {sells} sells)",
        f"  Round trips       : {n}",
        f"  Win rate          : {metrics.win_rate(result.trades) * 100:.1f}%",
        f"  Avg round-trip P&L: {avg_trip:+.2f}%",
        f"  Fees paid         : ${sum(t.fee for t in result.trades):,.2f}",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data" / "btcusdt_1h.csv"))
    ap.add_argument("--report", default=str(ROOT / "backtest_report.txt"))
    ap.add_argument("--curve", default=str(ROOT / "equity_curve.csv"))
    args = ap.parse_args()

    df = load_candles(args.data)
    print(f"Loaded {len(df)} candles: {df.index[0]} -> {df.index[-1]}")

    strategies = [SMACrossoverStrategy(20, 50), RSIMeanReversionStrategy(14, 30, 70)]
    results = {s.name: run_backtest(df, s, START_CASH) for s in strategies}

    blocks = ["CRYPTO TRADING BOT — BACKTEST REPORT",
              "=====================================",
              f"Symbol: BTCUSDT | Interval: 1h | Source: Binance public klines",
              f"Costs: 0.10% taker fee + 0.05% slippage per side",
              f"Execution: signal on bar t close -> filled at bar t+1 open",
              ""]
    for s in strategies:
        blocks.append(summarize(s.name, results[s.name], df))
        blocks.append("")
        blocks.append("  Trade list (timestamp, side, fill price, qty, notional, fee):")
        for t in results[s.name].trades:
            blocks.append(f"    {t.timestamp}  {t.side:4s}  ${t.price:>10,.2f}  "
                          f"{t.quantity:.6f} BTC  ${t.notional:>9,.2f}  fee ${t.fee:.2f}")
        blocks.append("")

    Path(args.report).write_text("\n".join(blocks))
    print(f"Wrote {args.report}")

    curve = pd.DataFrame({"timestamp": df.index, "btc_close": df["close"].values})
    for name, res in results.items():
        curve[f"equity_{name}"] = res.equity_curve.values
    curve.to_csv(args.curve, index=False)
    print(f"Wrote {args.curve}")

    for s in strategies:
        print()
        print(summarize(s.name, results[s.name], df))


if __name__ == "__main__":
    main()
