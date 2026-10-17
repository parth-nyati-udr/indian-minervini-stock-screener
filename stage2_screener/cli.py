"""Command-line entry point.

    stage2-screener stage2
    stage2-screener near-high
    stage2-screener rs-decline --since 2026-09-23
    stage2-screener bottoming --out results.csv
"""
from __future__ import annotations

import argparse

from . import data
from .screens import screen_bottoming, screen_near_high, screen_rs_in_decline, screen_stage2


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="stage2-screener")
    p.add_argument("screen", choices=["stage2", "near-high", "rs-decline", "bottoming"])
    p.add_argument("--since", help="reference date for rs-decline (YYYY-MM-DD)")
    p.add_argument("--period", default="2y")
    p.add_argument("--out", help="write results to CSV")
    a = p.parse_args(argv)
    if a.screen == "rs-decline" and not a.since:
        p.error("rs-decline needs --since")

    symbols = data.fetch_nifty500()["Symbol"].tolist()
    universe = data.download_ohlcv(symbols, period=a.period)
    last = max(df.index[-1] for df in universe.values()).date()
    print(f"Data as of {last} | {len(universe)}/{len(symbols)} symbols loaded")

    if a.screen == "stage2":
        res = screen_stage2(universe)
    elif a.screen == "near-high":
        res = screen_near_high(universe)
    elif a.screen == "bottoming":
        res = screen_bottoming(universe)
    else:
        bench = data.download_ohlcv([data.NIFTY500_INDEX], period=a.period)[data.NIFTY500_INDEX]
        res = screen_rs_in_decline(universe, bench["Close"], a.since)

    print(res.to_string(index=False) if len(res) else "No matches.")
    if a.out:
        res.to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
