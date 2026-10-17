"""Screen logic. Each `screen_*` takes {symbol: OHLCV DataFrame} and returns a
results DataFrame (one row per passing symbol), sorted strongest first.

OHLCV frames must have columns: Open, High, Low, Close, Volume.
"""
from __future__ import annotations

import pandas as pd

from . import indicators as ind
from .config import ScreenConfig

MIN_BARS = 260  # 200 SMA + 1 month of slope + buffer


def _has_history(df: pd.DataFrame, bars: int = MIN_BARS) -> bool:
    return df is not None and len(df.dropna(subset=["Close"])) >= bars


def compute_rs(universe: dict[str, pd.DataFrame]) -> pd.Series:
    """RS percentile for every symbol with enough history."""
    raw = {s: ind.rs_raw_score(df["Close"].dropna())
           for s, df in universe.items() if _has_history(df)}
    return ind.rs_percentile(pd.Series(raw, dtype=float).dropna())


# --------------------------------------------------------------------------
# Core building blocks
# --------------------------------------------------------------------------
def trend_template(df: pd.DataFrame, rs: float | None = None,
                   cfg: ScreenConfig = ScreenConfig()) -> dict[str, bool]:
    """Minervini Trend Template. Returns each criterion as a named boolean.

    RS is checked only when supplied, since it needs the whole universe.
    """
    c, h, l = df["Close"], df["High"], df["Low"]
    s50, s150, s200 = (ind.sma(c, n) for n in (cfg.sma_fast, cfg.sma_mid, cfg.sma_slow))
    last = c.iloc[-1]
    checks = {
        "price_above_150_200": last > s150.iloc[-1] and last > s200.iloc[-1],
        "sma150_above_200": s150.iloc[-1] > s200.iloc[-1],
        "sma200_rising": ind.is_rising(s200, cfg.sma_slow_rising_days),
        "sma50_above_150_200": s50.iloc[-1] > s150.iloc[-1] > s200.iloc[-1],
        "price_above_50": last > s50.iloc[-1],
        "above_52w_low": ind.pct_above_low(l, c) >= cfg.min_above_52w_low,
        "near_52w_high": ind.pct_from_high(h, c) <= cfg.max_below_52w_high,
    }
    if rs is not None:
        checks["rs_rating"] = rs >= cfg.min_rs_percentile
    return {k: bool(v) for k, v in checks.items()}


def stage2_status(df: pd.DataFrame, cfg: ScreenConfig = ScreenConfig()) -> dict:
    """v3 Stage 2 qualification with two routes.

    Route 1 (trending):      60-day persistence above 200 SMA >= threshold.
    Route 2 (consolidating): 125-day persistence >= threshold AND few 200 SMA
                             violations AND a tight 2-month range AND
                             up/down volume > 1 measured inside that range.
    Route 2 lets a strong trend that is merely basing qualify while
    excluding wide, sloppy drifts.
    """
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    s200 = ind.sma(c, cfg.sma_slow)
    w = cfg.consolidation_window
    m = {
        "p60": ind.persistence(c, s200, cfg.persistence_short),
        "p125": ind.persistence(c, s200, cfg.persistence_long),
        "violations": ind.ma_violations(c, s200, cfg.persistence_long),
        "range_2m": ind.range_pct(h, l, w),
        "updown_2m": ind.updown_volume_ratio(c, v, w),
    }
    trending = m["p60"] >= cfg.persistence_threshold
    consolidating = (m["p125"] >= cfg.persistence_threshold
                     and m["violations"] <= cfg.max_violations
                     and m["range_2m"] <= cfg.max_consolidation_range
                     and m["updown_2m"] > cfg.min_updown_volume)
    m["route"] = "trending" if trending else ("consolidating" if consolidating else None)
    m["passes"] = bool(trending or consolidating)
    return m


# --------------------------------------------------------------------------
# Screens
# --------------------------------------------------------------------------
def screen_stage2(universe: dict[str, pd.DataFrame],
                  cfg: ScreenConfig = ScreenConfig()) -> pd.DataFrame:
    """Full v3 screen: Trend Template + Stage 2 persistence, tiered A/B."""
    rs = compute_rs(universe)
    rows = []
    for sym, df in universe.items():
        if not _has_history(df) or sym not in rs:
            continue
        tt = trend_template(df, rs[sym], cfg)
        if not all(tt.values()):
            continue
        st = stage2_status(df, cfg)
        if not st["passes"]:
            continue
        c, h, v = df["Close"], df["High"], df["Volume"]
        s50, s200 = ind.sma(c, cfg.sma_fast), ind.sma(c, cfg.sma_slow)
        from_hi = ind.pct_from_high(h, c)
        ud50 = ind.updown_volume_ratio(c, v, 50)
        a14 = ind.atr(df["High"], df["Low"], c)
        rows.append({
            "symbol": sym,
            "close": round(c.iloc[-1], 2),
            "rs": rs[sym],
            "ext200_%": round(ind.extension(c, s200) * 100, 1),
            "vs50_%": round(ind.extension(c, s50) * 100, 1),
            "from_high_%": round(from_hi * 100, 1),
            "updown_50": round(ud50, 2),
            "p60": round(st["p60"], 2),
            "p125": round(st["p125"], 2),
            "violations": st["violations"],
            "route": st["route"],
            "atr_contraction": round(a14.iloc[-1] / a14.iloc[-126:].max(), 2),
            "vol_dryup": round(ind.volume_ratio(v, 10, 50), 2),
            "tier": "A" if (ud50 >= cfg.tier_a_updown and from_hi <= cfg.tier_a_from_high) else "B",
        })
    out = pd.DataFrame(rows)
    return out.sort_values(["tier", "rs"], ascending=[True, False]).reset_index(drop=True) if len(out) else out


def screen_near_high(universe: dict[str, pd.DataFrame],
                     cfg: ScreenConfig = ScreenConfig()) -> pd.DataFrame:
    """Stocks within `near_high_pct` of the 52-week high, with momentum context."""
    rows = []
    for sym, df in universe.items():
        if not _has_history(df):
            continue
        c, h, v = df["Close"], df["High"], df["Volume"]
        from_hi = ind.pct_from_high(h, c)
        if from_hi > cfg.near_high_pct:
            continue
        tt = trend_template(df, None, cfg)
        rows.append({
            "symbol": sym,
            "close": round(c.iloc[-1], 2),
            "from_high_%": round(from_hi * 100, 1),
            "ret_4w_%": round((c.iloc[-1] / c.iloc[-21] - 1) * 100, 1),
            "ret_3m_%": round((c.iloc[-1] / c.iloc[-63] - 1) * 100, 1),
            "ext50_%": round(ind.extension(c, ind.sma(c, cfg.sma_fast)) * 100, 1),
            "volx": round(ind.volume_ratio(v, cfg.volx_recent, cfg.volx_base), 2),
            "trend_template": all(tt.values()),
        })
    out = pd.DataFrame(rows)
    return out.sort_values("ret_3m_%", ascending=False).reset_index(drop=True) if len(out) else out


def screen_rs_in_decline(universe: dict[str, pd.DataFrame], benchmark: pd.Series,
                         since: str, cfg: ScreenConfig = ScreenConfig()) -> pd.DataFrame:
    """Stocks that rose since `since` while the benchmark fell, and are in Stage 2."""
    bench = benchmark.dropna()
    bench_ret = bench.iloc[-1] / bench.loc[:since].iloc[-1] - 1
    if bench_ret >= 0:
        raise ValueError(f"Benchmark is up {bench_ret:.1%} since {since}; no decline to test against.")
    rows = []
    for sym, df in universe.items():
        if not _has_history(df):
            continue
        c = df["Close"].dropna()
        ret = c.iloc[-1] / c.loc[:since].iloc[-1] - 1
        if ret <= 0 or not all(trend_template(df, None, cfg).values()):
            continue
        rows.append({
            "symbol": sym,
            "ret_since_%": round(ret * 100, 1),
            "excess_vs_bench_%": round((ret - bench_ret) * 100, 1),
            "from_high_%": round(ind.pct_from_high(df["High"], c) * 100, 1),
            "volx": round(ind.volume_ratio(df["Volume"], 5, 50), 2),
        })
    out = pd.DataFrame(rows)
    return out.sort_values("excess_vs_bench_%", ascending=False).reset_index(drop=True) if len(out) else out


def screen_bottoming(universe: dict[str, pd.DataFrame],
                     cfg: ScreenConfig = ScreenConfig()) -> pd.DataFrame:
    """Weinstein Stage 1 -> 2 candidates: deep decline, flattening 200 SMA,
    accumulation, price near the base pivot but still below the old high."""
    rows = []
    for sym, df in universe.items():
        if not _has_history(df):
            continue
        c, h, v = df["Close"], df["High"], df["Volume"]
        decline, peak_dt, trough_dt = ind.peak_to_trough_decline(c)
        if decline < cfg.min_decline:
            continue
        if ind.pct_from_high(h, c, window=len(h)) < cfg.min_below_2y_high:
            continue  # already recovered
        s200 = ind.sma(c, cfg.sma_slow)
        slope = s200.iloc[-1] / s200.iloc[-21] - 1
        if abs(slope) > cfg.max_slow_sma_slope:
            continue
        ud = ind.updown_volume_ratio(c, v, 50)
        if ud <= cfg.min_updown_volume:
            continue
        pivot = float(h.loc[trough_dt:].max())  # base high since the trough
        dist = pivot / c.iloc[-1] - 1
        if dist > cfg.max_distance_to_pivot:
            continue
        rows.append({
            "symbol": sym,
            "decline_%": round(decline * 100, 1),
            "peak": peak_dt.date(), "trough": trough_dt.date(),
            "pivot": round(pivot, 2),
            "to_pivot_%": round(dist * 100, 1),
            "sma200_slope_%": round(slope * 100, 2),
            "updown_50": round(ud, 2),
        })
    out = pd.DataFrame(rows)
    return out.sort_values("to_pivot_%").reset_index(drop=True) if len(out) else out
