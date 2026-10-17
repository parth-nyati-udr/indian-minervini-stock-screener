"""All screen thresholds in one place, so rules are explicit and tunable."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenConfig:
    # --- Moving averages (Minervini uses SMAs only) ---
    sma_fast: int = 50
    sma_mid: int = 150
    sma_slow: int = 200
    sma_slow_rising_days: int = 22          # 200 SMA must be rising for ~1 month

    # --- Trend Template price location ---
    min_above_52w_low: float = 0.30         # price >= 30% above 52-week low
    max_below_52w_high: float = 0.25        # price within 25% of 52-week high
    min_rs_percentile: float = 70.0         # IBD-style RS rating

    # --- Stage 2 persistence (v3) ---
    persistence_threshold: float = 0.80     # share of days closing above 200 SMA
    persistence_short: int = 60
    persistence_long: int = 125
    max_violations: int = 3                 # crosses below 200 SMA (consolidation route)
    consolidation_window: int = 42          # ~2 months
    max_consolidation_range: float = 0.15   # (high - low) / low within the window
    min_updown_volume: float = 1.0

    # --- Tiering ---
    tier_a_updown: float = 1.25
    tier_a_from_high: float = 0.15

    # --- Near-high momentum screen ---
    near_high_pct: float = 0.05
    volx_recent: int = 15
    volx_base: int = 50

    # --- Bottoming reversal screen ---
    min_decline: float = 0.30               # peak -> later trough
    min_below_2y_high: float = 0.10         # must still be below the old high
    max_slow_sma_slope: float = 0.02        # |20-day change in 200 SMA| -> "flattening"
    max_distance_to_pivot: float = 0.10
