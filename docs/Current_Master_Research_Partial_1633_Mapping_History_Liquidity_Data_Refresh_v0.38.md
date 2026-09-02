# Current Master Research Partial 1633 Mapping / History / Liquidity Data Refresh v0.38

## Scope

CURRENT_MASTER_RESEARCH_PARTIAL_1633_MAPPING_HISTORY_LIQUIDITY_DATA_REFRESH is a DEV / RESEARCH / SHADOW data-acquisition stage. The normal v0.38 path refreshes deterministic Yahoo provider mapping, daily OHLCV cache evidence, history QA, EOD FX, and median 20-session primary-market turnover in EUR for the frozen 1,633-row RESEARCH_PARTIAL current master.

It is not a productive eligibility, U3K, P0, sector-RS, news, event, fundamental, spread, broker, or trade-decision stage.

## Frozen baseline and immutability

The runner verifies configured Git blobs before network activity and again after output materialization. It also requires cleanup commit `52505152c9cb70bdebca58d9f7fd9c06bbd875f5` in `main`, requires the temporary v0.37 recovery workflow to be absent, and checks the v0.37 1,633-row baseline count gates.

The current master XLSX, `research_partial_1633.csv`, its manifest, the v0.37 handoff and v0.37 baseline outputs are read-only inputs. No universe or v0.37 content is written.

## Provider contract — normal v0.38 path

Only `YFINANCE_FREE` is used for this stage and only as a development acquisition provider. `BULK_OHLCV_PROVIDER` is not promoted. Alpha Vantage is forbidden and no key or fallback exists.

`scripts/price_cache.py` remains unchanged. The normal path reuses `FreeDataConfig`, `build_yahoo_symbol_map()`, `SQLitePriceCache`, `YFinanceBatchClient`, `YFinancePriceCacheRunner`, `normalize_symbol_frame()`, `technical_valid_mask()` and `qa_symbol_frame()`.

A deterministic multi-ticker smoke gate precedes the normal refresh. Normal history requests use cached runner multi-ticker batches of at most 100; one bounded rescue pass and targeted `repair=True` QA repair are inherited from the established runner. A broad provider failure opens a fail-closed circuit and prevents a successful handoff.

## Mapping and identity

Yahoo mapping is rebuilt from canonical WS_ID, primary ticker/MIC, existing explicit Yahoo symbol, and project overrides on the normal path. A provider symbol never changes WS_ID, ISIN, primary MIC/ticker, or identity baseline state.

No data does not create an override, ADR, secondary listing, guessed ticker or name-search substitution. It remains mapping pending/download-no-data and is placed in the remediation queue.

The 19 existing structural instrument FAILs remain output rows but receive no stock-data request.

## As-of, history, FX and liquidity — normal path

The normal v0.38 path uses the UTC calendar day before runtime start as safe global daily cutoff. Bars after it are excluded from QA, history and liquidity calculations.

History requires at least 260 unique and 252 valid completed bars for `PASS_HISTORY_CURRENT`. QA failures remain quarantine; stale, download, mapping and instrument states are explicit.

Currencies are normalized using the technical aliases from the historical FX reference. XLON quotes use scale 0.01. EUR is identity. Non-EUR FX requests use direct `CCYEUR=X`; the normal path retains its original semantics. No implicit USD triangulation is used. FX joins are backward-only and limited to ten calendar days.

Liquidity uses the last 20 valid completed primary-market sessions, needs at least 18 usable FX-converted sessions, and classifies median EUR turnover as preferred (>=20m), standard (>=15m), low-liquidity exception pool (>=5m), or fail (<5m). Current liquidity is evidence only; it cannot promote productive eligibility.

## Technical correction: FX_BATCH_AUDIT_ONLY

The v0.38 technical retry exists only to correct the post-run FX and provider-batch audit semantics from the successful pre-fix run. It is not v0.39 and it is not a new fachlicher stage.

Reference provenance is fixed:

- pre-fix Actions run: `33471051553`
- pre-fix result commit: `8eb1846f11e13a388a00838e44240372fa467aac`
- retry mode: `FX_BATCH_AUDIT_ONLY`
- safe global EOD cutoff: `2026-08-31`
- frozen cache path: `runtime_cache/v0_38/current_master_1633_market_prices.sqlite`
- frozen cache SHA-256: `d466ae08fc22c5bcae86dacb88759773565552cd58e17640d971d191c83311d0`
- expected cache rows: `price_daily=676550`, `cache_state=1614`, `batch_log=21`

The retry validates the cache before and after use and opens SQLite in read-only/query-only mode. Any path, SHA or table-count mismatch fails closed. The retry performs zero stock OHLCV network requests, does not execute provider smoke, does not call the normal `--run` path, does not invoke `fetch_prices()`, and does not run initial/incremental stock-cache acquisition.

### Frozen stock/core outputs

The following pre-fix outputs are byte/blob immutable during the retry and are checked against their pre-fix Git blobs:

- `mapping_revalidation_1633_v0.38.csv`
- `mapping_remediation_queue_v0.38.csv`
- `price_cache_status_1633_v0.38.csv`
- `history_gate_current_1633_v0.38.csv`
- `data_quality_exceptions_v0.38.csv`
- `market_asof_by_segment_v0.38.csv`

The retry reads the frozen mapping/history outputs and stock cache as evidence. It rematerializes only FX, liquidity, readiness, provider batch plan/actual audit, and dependent summary/checkpoint/manifest/runtime-audit/handoff outputs.

### Retry FX semantics

EUR is exactly identity with `FX_to_EUR=1.0`.  For liquidity-session conversion EUR is handled as a true reporting-currency identity, not as an as-of market series: every EUR stock session receives `FX_to_EUR=1.0`, `FX_Source_Symbol=EUR_IDENTITY`, `Direction=IDENTITY`, `FX_Date_Used=Session_Date` and `FX_Lag_Days=0`.  No backward lookup is performed for EUR.

This session-level rule is required because the compact FX coverage ledger intentionally contains only one EUR identity row at the safe cutoff. Applying the generic backward-only as-of lookup to earlier EUR stock sessions would incorrectly classify them as `LIQUIDITY_FX_UNRESOLVED`; that condition is explicitly forbidden by the retry gates.

For every non-EUR currency the retry first requests `CCYEUR=X`, normalizes the returned frame, removes invalid dates and invalid/non-positive close values, and filters to `<= 2026-08-31`. A currency is accepted as `FX_RESOLVED / DIRECT` only if usable rows remain after those checks.

If no usable direct rows remain, the retry requests `EURCCY=X`, performs the same validity/cutoff checks, and inverts the valid values. Only then can the currency be `FX_RESOLVED / REVERSE_INVERTED`.

If direct and reverse are both unusable, the currency is `FX_UNRESOLVED` with `Rows=0` and blank first/last dates. `FX_RESOLVED` with zero rows or invalid dates is forbidden. No USD triangulation is permitted. In particular, TWD can never be marked resolved merely because a direct symbol object existed before cutoff filtering.

FX joins into liquidity remain backward-only with a maximum ten-calendar-day lag.

### Provider batch audit correction

Plan and actual request evidence are separated:

- `provider_batch_plan_v0.38.csv` contains only the deterministic 31 planned NORMAL batches.
- `provider_batch_log_v0.38.csv` contains only the 21 actual SQLite `batch_log` requests.

Actual requests are classified as exactly 17 NORMAL, 3 RESCUE and 1 REPAIR. Requested-symbol attempts must sum to 1,614 NORMAL, 239 RESCUE and 7 REPAIR. No `PLAN-*` row may appear in the actual log.

The corrected summary therefore uses `provider_batch_count=21`, `provider_batch_plan_count=31`, `provider_rescue_count=3`, and `provider_repair_count=1` when the strong gates pass.

## Workflow isolation

The existing v0.38 workflow reads `run_mode` from the v0.38 config. Missing `run_mode` defaults to `NORMAL` so the historical normal path remains available.

For `FX_BATCH_AUDIT_ONLY`, the workflow skips Provider Smoke Gate, Mapping Materialization, Controlled Batch OHLCV Refresh, Price QA/history materialization steps tied to the normal runner, and the normal strong gates. It restores the v0.38 cache, runs only `--retry-fx-batch-audit`, then `--retry-strong-gates`, commits corrected outputs/handoffs only after those gates pass, and does not save a new stock-cache entry.

The config file is intentionally the final trigger file because a push changing only
`config/current_master_research_partial_1633_mapping_history_liquidity_data_refresh_v0.38.json`
starts this workflow.

## Retry strong gates

The retry strong gates are offline and perform no network access. They verify at minimum:

- frozen cache SHA/counts before and after retry;
- immutable core output blobs;
- 1,633 rows and 1,633 unique WS_ID in required current ledgers;
- 31 plan rows and 21 actual batch rows;
- actual request types exactly 17 NORMAL / 3 RESCUE / 1 REPAIR;
- requested-symbol attempts exactly 1,614 / 239 / 7;
- 15 expected FX currencies;
- every resolved currency has `Rows>0` and valid first/last dates no later than `2026-08-31`;
- every unresolved currency has `Rows=0` and blank first/last dates;
- EUR identity and no false-resolved TWD;
- every materialized EUR liquidity session has rate `1.0`, source/direction `EUR_IDENTITY/IDENTITY`, same-day FX date and zero lag;
- no EUR row may be `LIQUIDITY_FX_UNRESOLVED` or `BLOCKED_FX`;
- summary consistency, zero stock network requests in retry, cache read-only state, and non-productive flags;
- byte-identical `WELT-SWING-CURRENT-Handoff-v0.38.md` and `WELT-SWING-CURRENT-Handoff-CURRENT.md`.

## Success conditions

The normal path retains its existing success conditions. The technical retry succeeds only after `FX_BATCH_AUDIT_ONLY` strong gates pass. It may update corrected FX/liquidity/readiness/audit outputs and dependent metadata/handoffs, but it must not mutate universe, v0.37 inputs, frozen stock evidence, eligibility, P0, sector RS, SWING_U3K_FROZEN or productive status.

## Next-stage decision

Technical mapping/download/FX/QA gaps continue to lead to `CURRENT_MASTER_RESEARCH_PARTIAL_1633_DATA_GAP_REMEDIATION`. A clean technical state would lead to `CURRENT_MASTER_RESEARCH_PARTIAL_1633_CURRENT_ELIGIBILITY_RECOMPUTATION_AND_U3K_INPUT_PLAN`. Neither successor starts automatically. The retry itself does not start v0.39.
