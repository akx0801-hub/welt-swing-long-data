# Welt-Swing Long DEV — Non-READY Diagnostic v0.1

**Source run:** Full 3663 Price/Data INITIAL  
**Universe:** 3,663  
**READY:** 3,578  
**Non-READY:** 85  
**QUARANTINE:** 55  
**WARMUP:** 20  
**DOWNLOAD_FAILED:** 9  
**STALE:** 1  
**P0:** OFF  
**Productive authority:** NO  
**Alpha Vantage:** FORBIDDEN

## Purpose

This pass diagnoses only the 85 non-READY rows from the first full 3,663
price/data run.

It deliberately does **not** repeat the full price download. The previous run
already executed nine rescue attempts and 55 repair attempts. Repeating the
same bulk request before understanding the failures would add cost and noise.

## Data sources used

1. `output_full_3663/errors.csv`
2. `output_full_3663/coverage.json`
3. restored `runtime_cache/full_3663_prices.sqlite`
4. Yahoo Search **only** for the nine `DOWNLOAD_FAILED` rows and the one
   `STALE` row.

There is no `yf.download()`, no `Ticker.history()`, no OHLCV refresh, no Alpha
Vantage, and no paid provider.

## Diagnostic logic

### WARMUP

`INSUFFICIENT_HISTORY` with otherwise internally valid bars is classified as:

`ACCEPT_WARMUP_SHORT_HISTORY`

This does not promote the security to READY. It means the short history is a
known coverage limitation rather than a broken mapping.

### QUARANTINE — invalid OHLC/volume

The local SQLite bars are inspected directly. Isolated invalid bars are flagged
as candidates for a later QA-policy review only when all of these are true:

- at least 260 valid bars remain;
- no more than two invalid bars;
- invalid share <= 1%;
- last bar is fresh.

Classification:

`LIKELY_ISOLATED_INVALID_BARS_FILTERABLE`

This is important for the Korean cluster and similar cases. The diagnostic pass
does not automatically change cache status.

### QUARANTINE — suspicious returns

Absolute close-to-close moves above 50% are recomputed and exported with date,
previous close, current close and nearby split information.

If every suspicious return aligns with a nearby split event, the row is marked
as likely corporate-action related. Otherwise it stays:

`SUSPICIOUS_RETURN_RESEARCH_REQUIRED`

No suspicious-return security is auto-promoted.

### DOWNLOAD_FAILED

No new price request is made. Yahoo Search checks whether the exact equity
symbol still exists and records up to eight search candidates.

This helps separate:

- current symbol but price-endpoint issue;
- renamed/restructured provider symbol;
- stale constituent;
- delisted/acquired security.

Actual source/listing evidence remains a later targeted evidence step.

### STALE

The single stale row receives the same symbol/search diagnostic and remains a
listing/provider review item.

## Outputs

- `output_non_ready_diagnostic/summary_v0.1.json`
- `output_non_ready_diagnostic/non_ready_diagnostic_rows_v0.1.csv`
- `output_non_ready_diagnostic/non_ready_clusters_v0.1.csv`
- `output_non_ready_diagnostic/segment_status_counts_v0.1.csv`
- `output_non_ready_diagnostic/invalid_bar_events_v0.1.csv`
- `output_non_ready_diagnostic/suspicious_return_events_v0.1.csv`
- `output_non_ready_diagnostic/failed_stale_search_diagnostic_v0.1.csv`

## Governance

This step changes no provider mappings, no cache statuses and no universe
membership. It makes zero automatic READY promotions.

P0 remains disabled. The output is intended to tell us which small follow-up is
actually justified:

- accept WARMUP as a documented limitation;
- patch QA for isolated filterable bad bars;
- research genuine >50% events/corporate actions;
- repair or exclude stale/delisted provider failures.
