# Current Master BR IBrX100 Source Segment Freeze and Liquidity Precheck v0.32

## Status

DEV / RESEARCH / SHADOW — NOT PRODUCTIVE

Stage:

CURRENT_MASTER_BR_IBRX100_SOURCE_SEGMENT_FREEZE_AND_LIQUIDITY_PRECHECK

Welt-Swing v7.2 remains solely authoritative for productive Swing decisions.

This stage is not P0, not a productive Swing scan, not a canonical-master import and not an eligibility promotion. Alpha Vantage remains forbidden.

## Purpose

v0.32 converts the already reconciled official Brazil / IBrX 100 evidence from v0.31 into two reproducible frozen source-segment snapshots and runs a fail-closed liquidity precheck on the 79 Strict Ordinary candidates only.

The existing 1,535-row Current Master is not changed.

Global stage classification remains PARTIAL because the full 14-segment source superset is incomplete.

## Verified predecessor state

The stage requires and fail-closes on the following v0.31 state:

- lineage: CURRENT_MASTER_CLEAN_RESTART
- Current Master rows before/after: 1,535 / 1,535
- official B3 IBrX 100 membership: 98
- Identity PASS: 98
- Strict Ordinary candidates: 79
- Instrument FAIL: 19
  - Preferred Shares: 12
  - Units: 7
- Instrument NOT VERIFIED: 0
- Primary MIC: BVMF
- guessed ISIN: false
- B3 header.date: 31/08/26
- Source_AsOf_Official: 2026-08-31
- Source_AsOf_Semantics: OFFICIAL_B3_HEADER_DATE_UNINTERPRETED

Any deviation aborts the stage. It is not silently repaired.

## Frozen authoritative inputs

The GitHub Actions workflow pins the current Git blob SHA of each authoritative input:

| Input | Git blob SHA |
|---|---|
| docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md | 680d0434e534d1fe136e694ca05cb574958a1a24 |
| output_current_master_membership_identity_reconciliation_v0_31/summary_v0.31.json | 666f34eefe98758cf74192d0d58007dc0992ca4e |
| output_current_master_membership_identity_reconciliation_v0_31/stage_checkpoint_v0.31.json | 87dcca405b2a0dbbc7b1ad240e3d5ba61e39b2d1 |
| output_current_master_membership_identity_reconciliation_v0_31/br_ibrx100_identity_reconciliation_v0.31.csv | aeb03d77ae80818312cbeb70e2643bae1f521fde |
| output_current_master_membership_identity_reconciliation_v0_31/br_ibrx100_strict_ordinary_candidates_v0.31.csv | 92420932bf9c50ddc304442c03315003ac2a7b11 |
| output_current_master_membership_identity_reconciliation_v0_31/br_ibrx100_instrument_exclusions_v0.31.csv | 36bb83c56ed3ada1fab0d3c02179188abfdec227 |
| output_current_master_source_deep_materialization_v0_30/b3_ibrx100_official_raw_v0.30.json | efd5a73e52a9e3e54788fcad01efdd05222a23a0 |
| WELT-SWING-CURRENT-Handoff-CURRENT.md | 0f1c03957b00d704a4b2f408d813846b6cbbe269 |

The workflow recomputes each value with git hash-object before execution.

## Source-segment freeze

The stage creates:

- universe/segments/br_ibrx100_source_frozen_v0.32.csv
- universe/segments/br_ibrx100_strict_ordinary_frozen_v0.32.csv

The 98-row source freeze is byte-exact to the v0.31 identity reconciliation ledger.

The 79-row Strict Ordinary freeze is byte-exact to the v0.31 Strict Ordinary candidate ledger.

The 19 Instrument FAIL rows remain documented in v0.31 and are excluded from the Strict Ordinary freeze. No legacy Phase-2 membership and no third-party membership are added.

## Price and FX acquisition

Only the 79 Strict Ordinary candidates are queried.

- primary market: B3
- Primary MIC: BVMF
- equity provider: YFINANCE_FREE
- mapping: Primary_Ticker + .SA
- FX provider: YFINANCE_FREE
- FX symbol: EURBRL=X
- interval: daily
- requested lookback: 120 calendar days
- required valid sessions: 20
- current Brazil calendar day is excluded so that an incomplete current session cannot enter the calculation
- one automatic retry is allowed for a transient empty response or download error

No Alpha Vantage package, endpoint, symbol or fallback is used.

## Turnover method

For each valid primary-market session:

Turnover_BRL = Close_BRL × Volume

Turnover_EUR = Turnover_BRL / EURBRL

This is explicitly a PRICE_X_VOLUME_TURNOVER_APPROXIMATION. It is not a directly reported B3 turnover value.

EURBRL=X represents approximately BRL per EUR.

FX alignment is backward-only. Each B3 session receives the same-day FX value or the latest prior valid EURBRL value. No future FX value is permitted. Weekend or holiday gaps can therefore only be filled from a prior valid observation.

## Valid-session gate

A session is valid only when all of the following hold:

- completed session date
- Close_BRL > 0
- Volume > 0
- backward-aligned EURBRL > 0

MedianTurnover20_BRL and MedianTurnover20_EUR are calculated over the last 20 valid completed sessions.

If fewer than 20 valid sessions exist, no median is published and the security is classified as DATA_NOT_READY_QUARANTINE.

Every one of the 79 securities remains present in both the liquidity ledger and the data-quality ledger, including unresolved or quarantined mappings.

## Liquidity classes

The unchanged master thresholds are applied without a Brazil exception:

| MedianTurnover20_EUR | v0.32 class |
|---:|---|
| at least EUR 20 million | PASS_PREFERRED |
| at least EUR 15 million and below EUR 20 million | PASS_STANDARD |
| at least EUR 5 million and below EUR 15 million | LOW_LIQUIDITY_EXCEPTION_POOL |
| below EUR 5 million | FAIL_LIQUIDITY |
| data-quality or session gate not passed | DATA_NOT_READY_QUARANTINE |

LOW_LIQUIDITY_EXCEPTION_POOL is not an automatic Strict-U3K PASS.

PASS_PREFERRED and PASS_STANDARD are liquidity-precheck results only.

## Data-quality and mapping states

The result ledgers record at least:

- WS_ID
- Primary_MIC
- Primary_Ticker
- Yahoo_Symbol
- Security_Name
- Instrument_Type
- Source_AsOf_Official
- Price_AsOf
- Valid_Sessions
- MedianTurnover20_BRL
- MedianTurnover20_EUR
- EURBRL_AsOf
- Liquidity_Class
- Data_Quality_State
- Provider
- Mapping_State

Fail-closed states cover:

- unresolved Yahoo symbol
- wrong or unclear primary market
- mapping conflict
- no positive close
- no positive usable volume
- missing backward-aligned FX
- fewer than 20 valid completed sessions
- provider download failure

## Required outputs

Output directory:

output_current_master_br_ibrx100_liquidity_v0_32/

Files:

- br_ibrx100_liquidity_precheck_v0.32.csv
- br_ibrx100_price_data_quality_v0.32.csv
- br_ibrx100_price_history_v0.32.csv
- eurbrl_fx_history_v0.32.csv
- liquidity_class_counts_v0.32.csv
- summary_v0.32.json
- stage_checkpoint_v0.32.json
- manifest_v0.32.json

The two frozen segment files are stored under universe/segments/.

## Mandatory result gates

The stage asserts:

- source frozen rows = 98
- Strict Ordinary frozen rows = 79
- liquidity ledger rows = 79
- data-quality ledger rows = 79
- each Strict WS_ID and ticker appears exactly once
- no Preferred Share or Unit occurs in the Strict freeze
- Primary_MIC is BVMF
- Yahoo symbol equals Primary_Ticker.SA
- no ISIN is guessed
- MedianTurnover20_EUR exists only for READY rows with at least 20 valid sessions
- non-READY rows cannot receive a liquidity PASS
- liquidity classes are limited to the five defined values
- class counts sum to 79
- handoff files are byte-identical
- Current Master remains 1,535 rows
- stage remains PARTIAL
- no eligibility promotion
- no canonical import
- no universe mutation
- no P0
- no Sector RS
- no productive status
- no SWING_U3K_FROZEN
- Source Superset remains incomplete
- Alpha Vantage remains forbidden

## Governance flags

The following flags are hard-coded false and are also asserted by the result validator:

- Eligibility_Promotion_v0_32
- Canonical_Master_Import_v0_32
- Universe_Mutated
- P0
- Sector_RS
- Productive
- SWING_U3K_FROZEN
- Source_Superset_Complete
- Alpha_Vantage_Allowed

## Current Handoff

A technically successful run creates or updates:

- WELT-SWING-CURRENT-Handoff-v0.32.md
- WELT-SWING-CURRENT-Handoff-CURRENT.md

Both files must be byte-identical.

The handoff reports the frozen counts, all five liquidity result counts, actual Price_AsOf and EURBRL_AsOf, provider, approximation method, unchanged 1,535-row Current Master and all negative promotion/import/productive flags.

## Recovery and next stage

Recovery starts with the authoritative master, the CURRENT handoff, v0.32 checkpoint, v0.32 manifest, v0.32 summary, liquidity and data-quality ledgers, both frozen segments, then the v0.31 identity inputs and v0.30 official B3 raw snapshot.

After technical success the next PLAN stage is:

CURRENT_MASTER_BR_IBRX100_ELIGIBILITY_GATE_COMPLETION_AND_CONTROLLED_SEGMENT_IMPORT_PLAN

v0.32 does not start that stage and performs no canonical import.
