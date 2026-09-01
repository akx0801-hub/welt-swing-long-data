# Current Master Research Partial 1633 Mapping / History / Liquidity Data Refresh v0.38

## Scope

CURRENT_MASTER_RESEARCH_PARTIAL_1633_MAPPING_HISTORY_LIQUIDITY_DATA_REFRESH is a DEV / RESEARCH / SHADOW data-acquisition stage. It refreshes deterministic Yahoo provider mapping, daily OHLCV cache evidence, history QA, EOD FX, and median 20-session primary-market turnover in EUR for the frozen 1,633-row RESEARCH_PARTIAL current master.

It is not a productive eligibility, U3K, P0, sector-RS, news, event, fundamental, spread, broker, or trade-decision stage.

## Frozen baseline and immutability

The runner verifies configured Git blobs before network activity and again after output materialization. It also requires cleanup commit 52505152c9cb70bdebca58d9f7fd9c06bbd875f5 in main, requires the temporary recovery workflow to be absent, and checks the v0.37 1,633-row baseline count gates.

The current master XLSX, research_partial_1633.csv, its manifest, the v0.37 handoff and v0.37 baseline outputs are read-only inputs. No universe or v0.37 content is written.

## Provider contract

Only YFINANCE_FREE is used for this stage and only as a development acquisition provider. BULK_OHLCV_PROVIDER is not promoted. Alpha Vantage is forbidden and no key or fallback exists.

scripts/price_cache.py remains unchanged. The stage reuses FreeDataConfig, build_yahoo_symbol_map(), SQLitePriceCache, YFinanceBatchClient, YFinancePriceCacheRunner, normalize_symbol_frame(), technical_valid_mask() and qa_symbol_frame().

A deterministic multi-ticker smoke gate precedes the refresh. Normal history requests use cached runner multi-ticker batches of at most 100; one bounded rescue pass and targeted repair=True QA repair are inherited from the established runner. A broad provider failure opens a fail-closed circuit and prevents a successful handoff.

## Mapping and identity

Yahoo mapping is rebuilt from canonical WS_ID, primary ticker/MIC, existing explicit Yahoo symbol, and project overrides. Priority is project override, explicit, normalized derived rule, then derived rule. A provider symbol never changes WS_ID, ISIN, primary MIC/ticker, or identity baseline state.

No data does not create an override, ADR, secondary listing, guessed ticker or name-search substitution. It remains mapping pending/download-no-data and is placed in the remediation queue.

The 19 existing structural instrument FAILs remain output rows but receive no stock-data request.

## As-of, history, FX and liquidity

The safe global daily cutoff is the UTC calendar day before runtime start. Bars after it are excluded from all QA, history and liquidity calculations.

History requires at least 260 unique and 252 valid completed bars for PASS_HISTORY_CURRENT. QA failures remain quarantine; stale, download, mapping and instrument states are explicit.

Currencies are normalized using the technical aliases from the historical FX reference. XLON quotes use scale 0.01. EUR is identity. Non-EUR FX requests use direct CCYEUR=X; only when direct is absent may EURCCY=X be inverted. No implicit USD triangulation is used. FX joins are backward-only and limited to ten calendar days.

Liquidity uses the last 20 valid completed primary-market sessions, needs at least 18 usable FX-converted sessions, and classifies median EUR turnover as preferred (>=20m), standard (>=15m), low-liquidity exception pool (>=5m), or fail (<5m). Current liquidity is evidence only; it cannot promote productive eligibility.

## Success conditions

The workflow produces exactly one 1,633-row mapping, cache-status, history, liquidity and data-readiness ledger; the session-level liquidity audit, FX audit, batch audit, cache snapshot, summary, checkpoint and manifest are emitted under output_current_master_research_partial_1633_data_refresh_v0_38/.

Only after strong result gates pass are outputs and byte-identical v0.38/CURRENT handoffs committed. Cache SQLite is never committed; it is retained via Actions cache and artifact.

## Next-stage decision

Technical mapping/download/FX/QA gaps lead to CURRENT_MASTER_RESEARCH_PARTIAL_1633_DATA_GAP_REMEDIATION. A clean technical refresh leads to CURRENT_MASTER_RESEARCH_PARTIAL_1633_CURRENT_ELIGIBILITY_RECOMPUTATION_AND_U3K_INPUT_PLAN. Neither successor starts automatically.
