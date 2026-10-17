"""Synthetic OHLCV fixtures: deterministic, offline, shaped to hit each rule."""
import numpy as np
import pandas as pd
import pytest


def make_ohlcv(close, volume=None, spread=0.01):
    """Build an OHLCV frame from a close path; high/low = close +/- spread."""
    close = np.asarray(close, dtype=float)
    idx = pd.bdate_range("2024-01-01", periods=len(close))
    vol = np.full(len(close), 1_000_000.0) if volume is None else np.asarray(volume, float)
    return pd.DataFrame({
        "Open": close, "High": close * (1 + spread), "Low": close * (1 - spread),
        "Close": close, "Volume": vol,
    }, index=idx)


def wiggle(n, amp=0.004, seed=0):
    """Small deterministic noise so up/down days both exist."""
    return 1 + amp * np.sin(np.arange(n) * 1.7 + seed)


@pytest.fixture
def uptrend():
    """Steady 400-day advance: textbook Stage 2."""
    n = 400
    close = 100 * np.exp(np.linspace(0, 1.0, n)) * wiggle(n)
    vol = np.where(np.diff(close, prepend=close[0]) > 0, 1.5e6, 1.0e6)
    return make_ohlcv(close, vol)


@pytest.fixture
def downtrend():
    """Steady 400-day decline: Stage 4."""
    n = 400
    return make_ohlcv(200 * np.exp(np.linspace(0, -0.8, n)) * wiggle(n))


@pytest.fixture
def make():
    return make_ohlcv
