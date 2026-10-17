# Test plan

All tests are offline and deterministic: price paths are synthetic, shaped to hit or miss each rule.

Run: `pytest -q`

## Indicators (`tests/test_indicators.py`)
| Test | Verifies |
|---|---|
| `test_sma_basic` | SMA arithmetic and NaN warm-up |
| `test_is_rising` | Slope check, including insufficient data → False |
| `test_persistence` | Share of closes above MA |
| `test_violations_count_crossings_not_days` | Crossing events, not days below |
| `test_updown_volume_ratio` | Up-day vs down-day volume |
| `test_pivot_uses_intraday_high_not_close` | Regression: pivot from highs |
| `test_peak_to_trough_is_chronological` | Regression: trough must follow peak |
| `test_rs_percentile_bounds` | RS ranks in 1–99, ordering preserved |
| `test_volume_ratio` | VolX calculation |
| `test_atr_positive` | ATR well-formed |

## Screens (`tests/test_screens.py`)
| Test | Scenario | Expected |
|---|---|---|
| `test_trend_template_passes_uptrend` | Steady advance | All criteria pass |
| `test_trend_template_fails_downtrend` | Steady decline | 200 SMA not rising, price below |
| `test_trend_template_rs_gate` | RS 90 vs 50 | Pass vs fail |
| `test_stage2_trending_route` | Steady advance | Passes via trending route |
| `test_stage2_consolidation_route_tight_base_passes` | Uptrend then tight base with accumulation | Passes |
| `test_stage2_wide_sloppy_drift_fails` | Choppy around 200 SMA, distribution | Fails, violations > 3 |
| `test_screen_stage2_ranks_and_filters` | Mixed universe | Downtrend excluded, strongest ranked first |
| `test_screen_near_high` | Up vs down | Only uptrend returned |
| `test_screen_rs_in_decline` | Stock up, benchmark down | Returned with positive excess |
| `test_rs_in_decline_rejects_rising_benchmark` | Benchmark up | Raises `ValueError` |
| `test_screen_bottoming_finds_base_and_skips_recovered` | Crash+base vs crash+recovery | Only the base returned |
| `test_short_history_is_skipped` | 100 bars | Skipped, no crash |

## Manual / live checks (not automated, need network)
1. Full Nifty 500 run reports `Data as of` and loaded/total counts.
2. Spot-check 3 passing names on a broker chart: MA stack and pivot match.
3. Delisted or renamed symbols are skipped without failing the run.
