# Scope

## The ask
Turn a set of ad-hoc screening scripts, run repeatedly in research sessions, into one reusable, tested package that:
1. Encodes the Minervini Trend Template and a stricter Stage 2 persistence test exactly and transparently.
2. Supports four recurring questions (Stage 2 leaders, near-high momentum, relative strength in a decline, bottoming bases) from a single data download.
3. Makes every threshold explicit and adjustable.
4. Prevents previously found analytical bugs from recurring.

## In scope
- NSE equities, Nifty 500 universe (any symbol list works via `download_ohlcv`).
- Daily bars, end-of-day data from Yahoo Finance.
- Technical screening only: trend, persistence, relative strength, volume, base structure.
- Tabular output (console, CSV).

## Out of scope
- Fundamental or valuation analysis.
- Intraday data, order placement, portfolio sizing, backtesting (see the separate trading-system repo).
- Historical constituent lists (survivorship-free testing).
- Exact price levels for execution: those must be confirmed on a broker feed.

## Assumptions
- Adjusted prices are acceptable for structure and ranking.
- RS is computed relative to the screened universe, IBD-style (40/20/20/20 quarterly weighting), not against a single index.
- At least 260 sessions of history are required; newer listings are skipped.

## Success criteria
- All tests pass offline.
- A full Nifty 500 run completes in a few minutes and reports the data-as-of date.
- Every passing row shows the metrics that justified it.
