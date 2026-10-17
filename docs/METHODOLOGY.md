# Methodology

## 1. Trend Template (Minervini)
Uses only the 50, 150 and 200-day **simple** moving averages.

| # | Criterion | Default |
|---|---|---|
| 1 | Price above 150 and 200 SMA | |
| 2 | 150 SMA above 200 SMA | |
| 3 | 200 SMA rising | ≥ 22 sessions |
| 4 | 50 > 150 > 200 | |
| 5 | Price above 50 SMA | |
| 6 | Price above 52-week low | ≥ 30% |
| 7 | Price near 52-week high | within 25% |
| 8 | RS percentile | ≥ 70 |

Only the 200 SMA must be rising. Requiring all three averages to rise continuously wrongly excludes valid Stage 2 markets that are basing.

## 2. Stage 2 persistence (v3)
A stock that passes the template today may have crossed the 200 SMA repeatedly, which is Stage 3 behaviour. Two routes qualify:

- **Trending:** closed above the 200 SMA on ≥ 80% of the last 60 sessions.
- **Consolidating:** ≥ 80% over 125 sessions **and** ≤ 3 crosses below the 200 SMA **and** a 2-month high-low range ≤ 15% **and** up/down volume > 1.0 *measured inside that 2-month window*.

Why in-window volume: a trailing 50-day window includes the strength *before* the stall and hides selling during it. In one observed case the trailing ratio was 1.19 while the in-window ratio was 0.83.

Why violations are counted as *crossings*: one shallow dip lasting five days is one event, not five.

Caveat: for a stock 35%+ above its 200 SMA, "≤ 3 violations" is nearly automatic, so range and in-window volume carry the real weight.

## 3. Tiering
Tier A: up/down volume (50d) ≥ 1.25 **and** within 15% of the 52-week high. Everything else that passes is Tier B. Sorted by tier, then RS.

Diagnostic columns: `ext200_%`, `vs50_%` (extension), `atr_contraction` (current ATR ÷ 6-month max, lower = tighter), `vol_dryup` (10-day ÷ prior 50-day volume, lower = quieter).

## 4. Relative strength
Raw score = 0.4·r(63d) + 0.2·r(126d) + 0.2·r(189d) + 0.2·r(252d), ranked to 1–99 across the universe.

## 5. Bottoming (Weinstein Stage 1 → 2)
- Peak-to-trough decline ≥ 30%, with the trough **after** the peak.
- Still ≥ 10% below the 2-year high (not already recovered).
- 200 SMA flattening: |20-day change| ≤ 2%.
- Up/down volume (50d) > 1.0.
- Within 10% of the pivot = highest intraday high since the trough.

## 6. Price-level rules
- A pivot is the highest **intraday high**, never the highest close.
- Never resample to month-end to find highs and lows; it misses intramonth extremes.
- Bulk screening may use adjusted data; exact levels need raw OHLC and broker confirmation.

## Bugs found in earlier versions (now regression-tested)
| Bug | Symptom | Fix | Test |
|---|---|---|---|
| Pivot from `close.max()` | Pivot quoted at 903 vs true 910 | `high.max()` | `test_pivot_uses_intraday_high_not_close` |
| Drawdown ignored order | Fully recovered stock flagged as bottoming | Running-peak drawdown | `test_peak_to_trough_is_chronological` |
| Overly strict MA slope | Valid Stage 2 markets excluded | Only 200 SMA must rise | `test_trend_template_passes_uptrend` |
