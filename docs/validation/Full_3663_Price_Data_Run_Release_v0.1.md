# Welt-Swing Long DEV — Full 3663 Price/Data Run Release v0.1

**Release input:** Evidence-frozen master v0.7  
**Source rows:** 3,664  
**Active rows:** 3,663  
**Inactive rows:** 1 (MultiChoice stale/delisted source row)  
**Active provider mapping:** 3,663 / 3,663 = 100%  
**P0:** OFF  
**Productive trading authority:** NO  
**Alpha Vantage:** FORBIDDEN  
**Price provider:** yfinance / Yahoo Finance free batch path

## Purpose

This release authorizes the first full price/data collection run over all 3,663
active evidence-frozen securities.

It does **not** authorize P0, candidate ranking, news injection, P1–P5, portfolio
sizing, or productive trading.

The data run uses the already-existing free-data architecture:

- multi-ticker batch downloads;
- persistent SQLite cache;
- two-year initial daily history;
- incremental overlap on later reruns;
- raw OHLCV storage;
- local technical feature construction;
- bounded anomaly repair;
- READY / WARMUP / STALE / QUARANTINE / DOWNLOAD_FAILED diagnostics.

## Release gates

The workflow refuses to start unless the previous Evidence Freeze reports:

- `EVIDENCE_FREEZE_COMPLETE`;
- 3,664 master rows;
- 3,663 active rows;
- 3,663 active provider mappings;
- 0 active unresolved;
- 100% provider mapping;
- `price_run_candidate_coverage_ready=true`;
- P0 off;
- Alpha Vantage forbidden.

## Active price universe

`scripts/build_full_price_universe_3663.py` creates:

- `universe/full_price_universe_3663.csv`
- `universe/full_price_universe_3663_manifest.json`

Selection is intentionally simple: every `Active=True` row from the
evidence-frozen v0.7 master. There is no price, liquidity, setup, quality,
ranking, news, P0, or trading filter.

The builder also reports provider-symbol duplicates as diagnostics without
changing canonical identity.

## Runtime configuration

`config/run_config_full_3663.json` uses:

- mode: `auto`
- batch size: 100
- initial period: 2 years
- incremental overlap: 14 calendar days
- one-second pause between batches
- anomaly repair enabled
- SQLite cache: `runtime_cache/full_3663_prices.sqlite`
- output: `output_full_3663/`

A new cache therefore performs an INITIAL run. A restored cache performs an
INCREMENTAL run.

## Expected outputs

- `output_full_3663/coverage.json`
- `output_full_3663/mapping_audit.csv`
- `output_full_3663/cache_status.csv`
- `output_full_3663/errors.csv`
- `output_full_3663/batch_log_latest.csv`
- `output_full_3663/features_latest.csv`
- `output_full_3663/manifest.json`

The SQLite cache is retained through GitHub Actions cache and also included in
the run artifact for 14 days. It is not committed into the repository.

## Success interpretation

The workflow requires 3,663/3,663 provider mappings before the data call.

After the call, `COMPLETE` means every active security is READY. `PARTIAL` is
not automatically a failure: WARMUP, QUARANTINE, or isolated provider/download
issues must be inspected as diagnostics.

Only a systemic failure with zero READY securities is treated as a hard run
failure by the existing `assert_run_status.py`.

## What remains forbidden

- P0 execution;
- P0 parameter promotion;
- news/research enrichment;
- P1/P2/P3/P4/P5 strategy execution;
- productive buy/sell decisions;
- Alpha Vantage;
- paid-provider dependency.

After the full data run, the next step is to inspect actual READY coverage,
quarantines, failures, feature coverage, batch behavior, and any provider-symbol
collisions before proceeding with U3K selection or strategy validation.
