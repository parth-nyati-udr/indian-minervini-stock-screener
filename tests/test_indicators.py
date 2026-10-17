import numpy as np
import pandas as pd

from stage2_screener import indicators as ind


def s(values):
    return pd.Series(values, index=pd.bdate_range("2024-01-01", periods=len(values)), dtype=float)


def test_sma_basic():
    assert ind.sma(s([1, 2, 3, 4]), 2).tolist()[1:] == [1.5, 2.5, 3.5]


def test_is_rising():
    assert ind.is_rising(s(range(30)), 22)
    assert not ind.is_rising(s(range(30, 0, -1)), 22)
    assert not ind.is_rising(s([1, 2]), 22)  # not enough data


def test_persistence():
    close, ma = s([2, 2, 0, 2]), s([1, 1, 1, 1])
    assert ind.persistence(close, ma, 4) == 0.75


def test_violations_count_crossings_not_days():
    # above, below, below, below, above, below -> 2 crossings down
    close = s([2, 0, 0, 0, 2, 0])
    assert ind.ma_violations(close, s([1] * 6), 5) == 2


def test_updown_volume_ratio():
    close = s([10, 11, 10, 11])         # up, down, up
    vol = s([0, 300, 100, 300])
    assert ind.updown_volume_ratio(close, vol, 3) == 6.0


def test_pivot_uses_intraday_high_not_close():
    """Regression (GRANULES): pivot was quoted from the highest close (903)
    instead of the highest intraday high (910)."""
    close = s([890, 903, 895])
    high = s([900, 910, 905])
    assert ind.pivot_high(high, 3) == 910
    assert ind.pivot_high(high, 3) != close.max()


def test_peak_to_trough_is_chronological():
    """Regression (MEDANTA): low-before-high must NOT count as a decline."""
    recovered = s([50, 60, 80, 100])   # low came first, then a rally
    decline, _, _ = ind.peak_to_trough_decline(recovered)
    assert decline == 0

    crashed = s([100, 80, 60, 70])
    decline, peak, trough = ind.peak_to_trough_decline(crashed)
    assert round(decline, 2) == 0.40 and peak < trough


def test_rs_percentile_bounds():
    r = ind.rs_percentile(s([0.1, 0.5, -0.2, 0.3]))
    assert r.min() >= 1 and r.max() <= 99
    assert r.idxmax() == r.index[1]


def test_volume_ratio():
    vol = s([1] * 50 + [2] * 15)
    assert ind.volume_ratio(vol, 15, 50) == 2.0


def test_atr_positive():
    c = s(np.linspace(100, 110, 30))
    assert (ind.atr(c * 1.01, c * 0.99, c).dropna() > 0).all()
