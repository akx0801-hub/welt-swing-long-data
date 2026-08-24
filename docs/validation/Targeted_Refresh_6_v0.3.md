# Welt-Swing Long DEV — Targeted Refresh 6 v0.3

## Purpose

This step performs the separate targeted two-year refresh produced by
Non-READY Remediation v0.2.

Exactly six active canonical securities are refreshed:

- Block ASX — `XYZ.AX`
- Sigma Foods — `SIGMAFA.MX`
- Goodman NZ — `GNZ.NZ`
- IES Holdings — `IESC`
- Sasol ordinary — `SOL.JO`
- Monster Beverage — `MNST`

The target set is frozen by WS_ID and provider symbol. Any mismatch aborts the
run.

## Work-cache safety

The workflow restores the existing full SQLite cache and copies it to a
disposable work cache. Only in that work copy are the six target histories
purged and rebuilt from a fresh two-year yfinance batch.

This prevents old and new provider-symbol history from being mixed under one
canonical WS_ID, while keeping the previously validated cache untouched if the
target refresh has a hard failure.

The standard bounded rescue and targeted `repair=True` QA logic stays active.

## Cache promotion rule

The work cache is promoted back to the main cache only when no target ends as:

- `DOWNLOAD_FAILED`, or
- `MAPPING_PENDING`.

`READY`, `WARMUP`, `QUARANTINE`, and `STALE` remain visible diagnostic outcomes
and do not by themselves block promotion.

This is intentional: a recently renamed or restructured provider symbol can
legitimately expose fewer than 260 bars and therefore remain `WARMUP`.

## Outputs

- `output_targeted_refresh_6/summary_v0.3.json`
- `output_targeted_refresh_6/targeted_before_state_v0.3.csv`
- `output_targeted_refresh_6/targeted_before_price_counts_v0.3.csv`
- `output_targeted_refresh_6/targeted_after_state_v0.3.csv`
- `output_targeted_refresh_6/targeted_after_price_counts_v0.3.csv`
- `output_targeted_refresh_6/targeted_ready_features_v0.3.csv`
- `output_targeted_refresh_6/targeted_batch_log_v0.3.csv`
- `output_targeted_refresh_6/targeted_universe_v0.3.csv`
- `output_targeted_refresh_6/targeted_queue_frozen_v0.3.csv`
- `output_targeted_refresh_6/cache_promotion_status.txt`

## Governance

- yfinance/Yahoo free data only.
- Exactly six securities, not another full-universe download.
- Fresh two-year reload for every target.
- No Alpha Vantage.
- No paid provider.
- No P0.
- No P1–P5.
- No productive trading authority.

After this run, the actual six target states determine whether any mapping or
corporate-action issue remains. Only after that result should the 20-row
filtered-invalid-bar QA rule be considered for formal promotion.
