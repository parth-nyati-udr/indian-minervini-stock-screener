import numpy as np
import pytest

from stage2_screener import (ScreenConfig, screen_bottoming, screen_near_high,
                             screen_rs_in_decline, screen_stage2, stage2_status,
                             trend_template)
from conftest import make_ohlcv, wiggle


def test_trend_template_passes_uptrend(uptrend):
    assert all(trend_template(uptrend).values())


def test_trend_template_fails_downtrend(downtrend):
    tt = trend_template(downtrend)
    assert not tt["sma200_rising"] and not tt["price_above_150_200"]


def test_trend_template_rs_gate(uptrend):
    assert trend_template(uptrend, rs=90)["rs_rating"]
    assert not trend_template(uptrend, rs=50)["rs_rating"]


def test_stage2_trending_route(uptrend):
    st = stage2_status(uptrend)
    assert st["passes"] and st["route"] == "trending"


def test_stage2_consolidation_route_tight_base_passes():
    """BHEL-style: long uptrend, then a tight 2-month base with accumulation,
    briefly dipping under the 200 SMA (fails the 60-day route)."""
    n_up, n_base = 340, 60
    up = 100 * np.exp(np.linspace(0, 0.9, n_up))
    base = up[-1] * (1 + 0.04 * np.sin(np.arange(n_base) / 4))
    close = np.concatenate([up, base])
    vol = np.where(np.diff(close, prepend=close[0]) > 0, 1.4e6, 1.0e6)
    df = make_ohlcv(close, vol)
    cfg = ScreenConfig(persistence_threshold=0.80)
    st = stage2_status(df, cfg)
    assert st["range_2m"] <= cfg.max_consolidation_range
    assert st["passes"]


def test_stage2_wide_sloppy_drift_fails():
    """Kirloskar-style: choppy around the 200 SMA, wide range, distribution."""
    n = 400
    close = 100 + 15 * np.sin(np.arange(n) / 6)
    vol = np.where(np.diff(close, prepend=close[0]) > 0, 0.8e6, 1.2e6)
    st = stage2_status(make_ohlcv(close, vol))
    assert not st["passes"]
    assert st["violations"] > 3


def test_screen_stage2_ranks_and_filters(uptrend, downtrend):
    # three uptrends of different strength so RS percentiles spread out
    uni = {"DOWN": downtrend, "UP": uptrend}
    n = 400
    for k, g in {"WEAK": 0.3, "MID": 0.6}.items():
        uni[k] = make_ohlcv(100 * np.exp(np.linspace(0, g, n)) * wiggle(n, seed=len(k)))
    res = screen_stage2(uni)
    assert "DOWN" not in res["symbol"].values
    assert res.iloc[0]["symbol"] == "UP"
    assert set(res["tier"]) <= {"A", "B"}


def test_screen_near_high(uptrend, downtrend):
    res = screen_near_high({"UP": uptrend, "DOWN": downtrend})
    assert res["symbol"].tolist() == ["UP"]


def test_screen_rs_in_decline(uptrend, downtrend):
    bench = downtrend["Close"]
    since = str(uptrend.index[-20].date())
    res = screen_rs_in_decline({"UP": uptrend, "DOWN": downtrend}, bench, since)
    assert res["symbol"].tolist() == ["UP"]
    assert (res["excess_vs_bench_%"] > 0).all()


def test_rs_in_decline_rejects_rising_benchmark(uptrend):
    with pytest.raises(ValueError):
        screen_rs_in_decline({"UP": uptrend}, uptrend["Close"], str(uptrend.index[-20].date()))


def test_screen_bottoming_finds_base_and_skips_recovered():
    # BASE: crash 45%, then long flat base, now pressing the base high
    crash = np.linspace(200, 110, 150)
    flat = 110 * (1 + 0.03 * np.sin(np.arange(250) / 5))
    base = np.concatenate([crash, flat])
    vol = np.where(np.diff(base, prepend=base[0]) > 0, 1.3e6, 1.0e6)
    # RECOVERED: same crash but already back at the high
    rec = np.concatenate([crash, np.linspace(110, 205, 250)])
    res = screen_bottoming({"BASE": make_ohlcv(base, vol), "RECOVERED": make_ohlcv(rec)})
    assert res["symbol"].tolist() == ["BASE"]
    assert res.iloc[0]["decline_%"] >= 30


def test_short_history_is_skipped():
    short = make_ohlcv(np.linspace(100, 120, 100))
    assert screen_near_high({"NEW": short}).empty
