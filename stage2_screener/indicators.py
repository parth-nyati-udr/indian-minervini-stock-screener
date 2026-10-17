"""Pure, vectorised indicator functions.

Every function takes pandas Series indexed by date and has no I/O, so each
is unit-testable on synthetic data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average; NaN until `window` observations exist."""
    return series.rolling(window, min_periods=window).mean()


def is_rising(series: pd.Series, lookback: int) -> bool:
    """True if the latest value is above the value `lookback` bars ago."""
    s = series.dropna()
    if len(s) <= lookback:
        return False
    return bool(s.iloc[-1] > s.iloc[-1 - lookback])


def persistence(close: pd.Series, ma: pd.Series, window: int) -> float:
    """Fraction of the last `window` sessions that closed above `ma`."""
    above = (close > ma).iloc[-window:]
    return float(above.mean()) if len(above) else np.nan


def ma_violations(close: pd.Series, ma: pd.Series, window: int) -> int:
    """Number of times price crossed from above to below `ma` in `window` bars.

    Counts crossing events rather than days below, so one shallow dip counts
    as 1, not as however many days it lasted.
    """
    above = (close > ma).iloc[-(window + 1):]
    crosses_down = above.shift(1, fill_value=False) & ~above
    return int(crosses_down.iloc[1:].sum())


def updown_volume_ratio(close: pd.Series, volume: pd.Series, window: int) -> float:
    """Volume on up-closes divided by volume on down-closes over `window` bars.

    Measure this INSIDE the window being judged; a trailing window that
    includes earlier strength masks selling during a stall.
    """
    chg = close.diff().iloc[-window:]
    vol = volume.iloc[-window:]
    up, down = vol[chg > 0].sum(), vol[chg < 0].sum()
    return float(up / down) if down > 0 else np.inf


def pivot_high(high: pd.Series, window: int) -> float:
    """Breakout pivot = highest INTRADAY high in the window (never the highest close)."""
    return float(high.iloc[-window:].max())


def pct_from_high(high: pd.Series, close: pd.Series, window: int = 252) -> float:
    """Fractional distance of the last close below the window's intraday high."""
    return float(1 - close.iloc[-1] / high.iloc[-window:].max())


def pct_above_low(low: pd.Series, close: pd.Series, window: int = 252) -> float:
    """Fractional distance of the last close above the window's intraday low."""
    return float(close.iloc[-1] / low.iloc[-window:].min() - 1)


def range_pct(high: pd.Series, low: pd.Series, window: int) -> float:
    """(max high - min low) / min low over the window: base tightness."""
    return float(high.iloc[-window:].max() / low.iloc[-window:].min() - 1)


def extension(close: pd.Series, ma: pd.Series) -> float:
    """How far the last close sits above `ma` (0.10 = 10% extended)."""
    return float(close.iloc[-1] / ma.iloc[-1] - 1)


def peak_to_trough_decline(close: pd.Series) -> tuple[float, pd.Timestamp, pd.Timestamp]:
    """Largest decline where the trough comes AFTER the peak.

    Fixes the classic bug of comparing a window low to a window high
    regardless of order, which flags stocks that already fully recovered.
    Returns (decline, peak_date, trough_date).
    """
    running_peak = close.cummax()
    drawdown = close / running_peak - 1
    trough_date = drawdown.idxmin()
    peak_date = close.loc[:trough_date].idxmax()
    return float(-drawdown.min()), peak_date, trough_date


def rs_raw_score(close: pd.Series) -> float:
    """IBD-style weighted 12-month return (40% latest quarter, 20% each prior)."""
    def ret(n: int) -> float:
        return close.iloc[-1] / close.iloc[-1 - n] - 1 if len(close) > n else np.nan
    return 0.4 * ret(63) + 0.2 * ret(126) + 0.2 * ret(189) + 0.2 * ret(252)


def rs_percentile(scores: pd.Series) -> pd.Series:
    """Convert raw RS scores to a 1-99 percentile rank across the universe."""
    return (scores.rank(pct=True) * 98 + 1).round(0)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """Average True Range (simple average of true range)."""
    prev = close.shift(1)
    tr = pd.concat([high - low, (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    return tr.rolling(window, min_periods=window).mean()


def volume_ratio(volume: pd.Series, recent: int, base: int) -> float:
    """Avg volume of the last `recent` bars vs the `base` bars before them (VolX)."""
    rec = volume.iloc[-recent:].mean()
    prior = volume.iloc[-(recent + base):-recent].mean()
    return float(rec / prior) if prior > 0 else np.nan
