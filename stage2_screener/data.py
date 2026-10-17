"""Data access: NSE constituents + yfinance OHLCV. The only module doing I/O."""
from __future__ import annotations

import io
import pickle
from pathlib import Path

import pandas as pd
import requests

NIFTY500_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
BROWSER_UA = {"User-Agent": "Mozilla/5.0"}  # NSE returns 403 without one
NIFTY500_INDEX = "^CRSLDX"
NIFTY50_INDEX = "^NSEI"


def fetch_nifty500() -> pd.DataFrame:
    """Current Nifty 500 constituents (Symbol, Company Name, Industry).

    Note: a current-constituents snapshot, so results carry survivorship bias.
    """
    resp = requests.get(NIFTY500_URL, headers=BROWSER_UA, timeout=30)
    resp.raise_for_status()
    return pd.read_csv(io.StringIO(resp.text))


def download_ohlcv(symbols: list[str], period: str = "2y", suffix: str = ".NS",
                   auto_adjust: bool = True, chunk: int = 100) -> dict[str, pd.DataFrame]:
    """Download daily OHLCV and return {symbol: DataFrame}.

    auto_adjust=True is fine for bulk screening. For pinning exact pivot or
    stop levels use auto_adjust=False, then verify on the broker chart.
    """
    import yfinance as yf

    out: dict[str, pd.DataFrame] = {}
    for i in range(0, len(symbols), chunk):
        batch = symbols[i:i + chunk]
        tickers = [s if s.startswith("^") else s + suffix for s in batch]
        raw = yf.download(tickers, period=period, auto_adjust=auto_adjust,
                          group_by="ticker", progress=False, threads=True)
        for sym, tkr in zip(batch, tickers):
            # group_by="ticker" yields a MultiIndex; older yfinance returns
            # flat columns for a single ticker.
            if isinstance(raw.columns, pd.MultiIndex):
                if tkr not in raw.columns.get_level_values(0):
                    continue
                df = raw[tkr]
            else:
                df = raw
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
            if len(df):
                out[sym] = df
    return out


def cache(obj, path: str | Path) -> None:
    """Pickle intermediate data so iterative analysis doesn't re-download."""
    Path(path).write_bytes(pickle.dumps(obj))


def load_cache(path: str | Path):
    return pickle.loads(Path(path).read_bytes())
