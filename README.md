# stage2-screener

Systematic **Minervini Trend Template + Weinstein Stage Analysis** screening for Indian equities (Nifty 500), with four screens sharing one data layer and one set of tested indicator functions.

| Screen | Question it answers |
|---|---|
| `stage2` | Which stocks are in a confirmed, persistent Stage 2 advance? Tiered A/B with RS, extension, accumulation, ATR contraction and volume dry-up. |
| `near-high` | Which stocks are within 5% of their 52-week high, and how extended are they? |
| `rs-decline` | Which Stage 2 stocks went **up** while the market fell since a given date? |
| `bottoming` | Which stocks are completing a Stage 1 base after a ≥30% decline (Stage 1→2 candidates)? |

## Install
```bash
pip install -e ".[dev]"
```

## Usage
```bash
stage2-screener stage2
stage2-screener near-high --out near_high.csv
stage2-screener rs-decline --since 2026-09-23
stage2-screener bottoming
```
Or in Python:
```python
from stage2_screener import data, screen_stage2, ScreenConfig

universe = data.download_ohlcv(data.fetch_nifty500()["Symbol"].tolist())
results = screen_stage2(universe, ScreenConfig(min_rs_percentile=80))
```
Every threshold lives in `ScreenConfig` (`stage2_screener/config.py`).

## Project layout
```
stage2_screener/
  config.py      all thresholds, one frozen dataclass
  indicators.py  pure functions: SMA, persistence, violations, U/D volume, pivots, RS, ATR
  screens.py     trend_template, stage2_status and the four screens
  data.py        NSE constituents + yfinance download (the only I/O module)
  cli.py         command-line entry point
tests/           22 offline tests on synthetic price paths
docs/            SCOPE.md, METHODOLOGY.md, TEST_PLAN.md
```

## Design choices
- **Pure indicators, I/O isolated.** Every rule is testable without a network.
- **Rules as named booleans.** `trend_template()` returns each criterion separately, so you can see *why* a stock failed.
- **Regression tests for real bugs.** Two historical errors (close-based pivots, non-chronological drawdowns) are locked in as tests.

## Limitations
Yahoo Finance data is end-of-day and adjusted; it is fine for bulk screening, not for exact levels. Verify pivots and stops on a broker chart before acting. The universe is today's Nifty 500, so results carry survivorship bias. This is a research tool, not investment advice.

## License
MIT
