# Welt-Swing Long DEV — U3K Liquidity / FX Eligibility Audit v0.5

## Purpose

This is the first strict-Universe eligibility pass after the successful
QA-filtered-bar promotion.

It follows Swing Long DEV v0.1 sections 13–17:

- primary-market liquidity is the central standard U3K gate;
- `MedianTurnover20_EUR >= 15m EUR` is standard PASS;
- `5m–15m EUR` belongs to a low-liquidity exception pool, not the normal
  automated Strict U3K;
- `<5m EUR` is FAIL;
- at least 18 usable sessions out of the latest 20 are required;
- free-float market cap is recorded as QA/research metadata and is **not** a
  standalone Swing Long hard gate;
- if more than 3,000 securities are fully eligible, the cap order is:
  20D EUR turnover, 60D EUR turnover, reliable free-float market cap if
  available, then WS_ID.

P0 remains OFF.

## Why this is an audit before a freeze

The current remediated master contains explicit `Instrument_Type` values.
Swing Long DEV v0.1 does not allow an unverified/unknown instrument type to
silently PASS a Strict Universe gate.

Therefore this workflow calculates the expensive missing liquidity/FX layer
first, then separates:

1. standard-liquidity READY securities;
2. explicit common/ordinary instrument PASS;
3. instrument review cases;
4. low-liquidity exception cases;
5. non-READY data exclusions.

A `SWING_U3K_FROZEN_v0.5.csv` is populated only if no otherwise-eligible
standard-liquidity row still has an unresolved instrument gate.

This prevents a provisional source-superset label from becoming a hidden
production eligibility assumption.

## FX architecture

FX is **not** queried per stock.

The workflow extracts the distinct primary currencies from the 3,657 active
master rows and downloads them in one Yahoo/yfinance batch as `CCY/EUR`.

If a direct pair is missing, one bounded reverse-pair batch (`EUR/CCY`) is
attempted and inverted.

The current-day partial FX candle is excluded. For this run the completed FX
cutoff is 2026-08-23, which means the latest normal FX observation should be
Friday 2026-08-21.

Daily stock turnover is converted with the most recent available EOD FX rate
on or before each session date.

## Quote-unit normalization

Two source markets require explicit major-currency scaling before EUR
conversion:

- London (`XLON`): Yahoo `.L` price quotes are treated as pence, scale `0.01`
  to GBP.
- Johannesburg (`XJSE`): Yahoo `.JO` price quotes are treated as cents, scale
  `0.01` to ZAR.

The raw price cache itself is not rewritten.

## Turnover calculation

For each READY security:

`DailyTurnoverMajorNative = raw_close × raw_volume × quote_scale`

Invalid OHLC/volume bars are excluded using the same technical-validity mask
already used by the promoted feature pipeline.

The last 20 and last 60 valid sessions are then FX-normalized to EUR.

Outputs include:

- `MedianTurnover20_EUR`
- `MedianTurnover60_EUR`
- usable-session counts
- FX coverage counts
- liquidity bucket/gate

No stock-price history is downloaded in this step.

## Instrument gate

Explicit PASS values in v0.5 are:

- `COMMON_STOCK`
- `ORDINARY_SHARE`
- `COMMON_SHARE`

Explicit preferred/fund/ETF/unit/warrant/right/debt-like types FAIL.

Everything else is `NOT_VERIFIED` and enters the instrument-review queue.

This is deliberately conservative. It does not infer common-stock status from
a company name or from price availability.

## Free-float market cap

Swing Long DEV v0.1 does **not** use a 2bn-EUR free-float market-cap hard gate.

The field is kept in the output but v0.5 marks it:

`NOT_COLLECTED_BULK_RELIABLY_QA_ONLY`

This is not a data-quality failure and does not independently exclude a stock.

A later reliable bulk source may populate it as QA metadata and as the tertiary
tie-break key in the 3,000 cap.

## Expected source state

- active remediated master: 3,657
- operational cache states: 3,657
- READY: 3,602
- QUARANTINE: 34
- WARMUP: 20
- STALE: 1

## Outputs

- `output_u3k_liquidity_fx_v0_5/summary_v0.5.json`
- `output_u3k_liquidity_fx_v0_5/eligibility_rows_v0.5.csv`
- `output_u3k_liquidity_fx_v0_5/fx_history_to_eur_v0.5.csv`
- `output_u3k_liquidity_fx_v0_5/fx_meta_v0.5.json`
- `output_u3k_liquidity_fx_v0_5/instrument_review_queue_v0.5.csv`
- `output_u3k_liquidity_fx_v0_5/low_liquidity_exception_pool_v0.5.csv`
- `output_u3k_liquidity_fx_v0_5/non_ready_exclusions_v0.5.csv`
- `output_u3k_liquidity_fx_v0_5/segment_gate_counts_v0.5.csv`
- `universe/SWING_U3K_PROVISIONAL_LIQUIDITY_POOL_v0.5.csv`
- `universe/SWING_U3K_FROZEN_v0.5.csv`
- `universe/SWING_U3K_Eligibility_Audit_v0.5.xlsx`

## Governance

- Yahoo/yfinance free data only for the small FX batch.
- Existing stock-price cache only; no new stock OHLCV download.
- No Alpha Vantage.
- No paid provider.
- No stock-by-stock web research.
- No P0.
- No P1–P5.
- No productive trade authority.

The actual output counts determine the next narrow step. If the instrument
review queue is material, only that queue is remediated next; the entire
3,657-row universe is not re-researched.
