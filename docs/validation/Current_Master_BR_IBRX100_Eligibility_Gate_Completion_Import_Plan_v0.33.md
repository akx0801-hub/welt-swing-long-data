# Current Master BR IBrX100 Eligibility Gate Completion and Controlled Import Plan v0.33

## Stage identity

- Stage: CURRENT_MASTER_BR_IBRX100_ELIGIBILITY_GATE_COMPLETION_AND_CONTROLLED_SEGMENT_IMPORT_PLAN
- Version: v0.33
- Status: DEV / RESEARCH / SHADOW - NOT PRODUCTIVE
- Lineage: CURRENT_MASTER_CLEAN_RESTART
- Global classification: PARTIAL
- Productive authority: Welt-Swing v7.2 only

This stage completes the currently testable standard eligibility hard gates for Brazil and creates a controlled SOURCE_SUPERSET import plan. It does not change the Current Master, research_partial_1535.csv, SWING_U3K_FROZEN or any productive state.

## Verified starting point

The following v0.32 facts are frozen and asserted fail-closed:

- Current Master rows: 1,535
- Official BR_IBRX100 source frozen: 98
- Strict Ordinary frozen: 79
- Instrument FAIL: 19
  - Preferred Shares: 12
  - Units: 7
- PASS_PREFERRED: 28
- PASS_STANDARD: 10
- LOW_LIQUIDITY_EXCEPTION_POOL: 28
- FAIL_LIQUIDITY: 13
- DATA_NOT_READY_QUARANTINE: 0
- Standard-liquidity candidates: 38
- Price_AsOf v0.32: 2026-08-27
- EURBRL_AsOf v0.32: 2026-08-27
- Provider: YFINANCE_FREE
- Alpha Vantage allowed: false

Any mismatch stops the stage.

## Frozen Git blob gates

The workflow checks current Git blob SHAs before execution:

| Input | Git blob SHA |
|---|---|
| docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md | 680d0434e534d1fe136e694ca05cb574958a1a24 |
| WELT-SWING-CURRENT-Handoff-CURRENT.md | 6c89d8bf69a5cd4d7a0c522d836d9587ce052d42 |
| output_current_master_br_ibrx100_liquidity_v0_32/summary_v0.32.json | 59e2fe0a2ebcb07a818071e065b8f16883cfabdb |
| output_current_master_br_ibrx100_liquidity_v0_32/stage_checkpoint_v0.32.json | 02a23ebcb68827f57b764629c69e096813f4e9b8 |
| output_current_master_br_ibrx100_liquidity_v0_32/br_ibrx100_liquidity_precheck_v0.32.csv | c03010329f7f74fca50576d9be5e0250cf3b0fd9 |
| universe/segments/br_ibrx100_source_frozen_v0.32.csv | aeb03d77ae80818312cbeb70e2643bae1f521fde |
| universe/segments/br_ibrx100_strict_ordinary_frozen_v0.32.csv | 92420932bf9c50ddc304442c03315003ac2a7b11 |
| output_current_master_membership_identity_reconciliation_v0_31/br_ibrx100_identity_reconciliation_v0.31.csv | aeb03d77ae80818312cbeb70e2643bae1f521fde |
| universe/Welt-Swing-Universe-Master-v2.0.xlsx | 0d58014169873ac0ee52ca739a60e09f8bd5799f |

The current GitHub short blob identifier for the XLSX was verified as 0d58014 and matched against the complete previously pinned Git blob. No hash was inferred from a filename or copied without current verification.

## Actual Current-Master workbook structure

The current XLSX blob is unchanged and contains these sheets:

- Universe_Master
- Import_Coverage
- Dedupe_Rules
- Status_Definitions
- Run_Summary

The stage reads Universe_Master with openpyxl and asserts its exact current 22-column order before creating a projection:

1. WS_ID
2. Name
3. ISIN
4. Instrument_Type
5. Country
6. Primary_Ticker
7. Primary_Exchange
8. Primary_MIC
9. Primary_Currency
10. Yahoo_Symbol
11. Alpha_Symbol
12. Primary_Universe_Index
13. Index_Tags
14. Active
15. Universe_Status
16. Mapping_Status
17. Scalable_Tradeability_Status
18. Source_ID
19. Source_AsOf
20. Last_Validated
21. Share_Class
22. Notes

A changed sheet or column structure fails closed. The output master projection uses exactly these columns and no eligibility or audit extension columns.

## Strict set separation

Four source and eligibility levels remain distinct:

| Set | Rows | v0.33 treatment |
|---|---:|---|
| Official BR source superset | 98 | All rows remain in the controlled import plan |
| Strict Ordinary Shares | 79 | Instrument-pass population |
| Standard-liquidity pass | 38 | Only population downloaded for the standard history gate |
| Low-liquidity exception pool | 28 | Preserved without history promotion |

The 13 FAIL_LIQUIDITY rows and 19 instrument fails remain SOURCE_SUPERSET members. They are not standard eligibility passes.

## History gate

Only PASS_PREFERRED and PASS_STANDARD rows from v0.32 enter the history download.

- Primary market: B3
- MIC: BVMF
- Yahoo mapping: Primary_Ticker plus .SA
- Provider: YFINANCE_FREE
- History request window: 1,100 calendar days
- Interval: daily
- Intraday data: not used
- Current Brazil session: excluded
- Future data: excluded
- Predecessor ticker substitution: forbidden
- ADR or secondary listing substitution: forbidden
- Company-name history reconstruction: forbidden

A completed Daily Bar is valid only if:

- Date is unique
- Close greater than zero
- High greater than zero
- Low greater than zero
- Volume greater than zero
- High greater than or equal to Low

Standard history requires both:

- at least 260 unique Daily Bars
- at least 252 valid completed Daily Bars

History states:

- PASS_HISTORY_STANDARD_U3K
- INSUFFICIENT_HISTORY_FOR_STANDARD_U3K
- DATA_QUALITY_FAIL_HISTORY
- DOWNLOAD_FAILED

A security with insufficient or failed history can never become STANDARD_ELIGIBILITY_READY.

## Standard eligibility plan

For the 38 standard-liquidity candidates the stage combines:

- source membership gate
- identity gate
- instrument gate
- liquidity class
- Yahoo mapping and market consistency
- history gate

STANDARD_ELIGIBILITY_READY is assigned only if every hard gate passes. This state means that all currently testable standard hard gates passed. It is a planning state only.

The following remain false:

- Eligibility_Promotion_v0_33
- Canonical_Master_Import_v0_33
- Universe_Mutated
- P0
- Sector_RS
- Productive
- SWING_U3K_FROZEN
- Source_Superset_Complete
- Alpha_Vantage_Allowed

## Scalable treatment

No live Scalable calls are made for either 38 or 98 rows. In the absence of authoritative cached evidence every Brazil row remains:

SCALABLE_NOT_VERIFIED

This plan state is never silently converted to verified or plausible. Current bid/ask verification belongs to the later P5 execution context.

## Controlled SOURCE_SUPERSET import plan

br_ibrx100_controlled_master_import_plan_v0.33.csv contains all 98 official source members.

Instrument and liquidity failures remain visible with:

ADD_TO_SOURCE_SUPERSET_ONLY

Rows that pass all current standard gates may be marked:

ADD_TO_SOURCE_SUPERSET_WITH_STANDARD_ELIGIBILITY_READY_PLAN_STATE

Neither action is executed in v0.33.

The 98-row master projection uses:

- Country: Brazil
- Primary_Exchange: B3
- Primary_MIC: BVMF
- Primary_Currency: BRL
- Primary_Universe_Index: BR_IBRX100
- Index_Tags containing BR_IBRX100
- Source_ID: B3_OFFICIAL_INDEXPROXY_GETPORTFOLIODAY
- Source_AsOf: 2026-08-31
- Alpha_Symbol: empty
- ISIN: empty unless already present in the authoritative frozen source
- WS_ID: stable v0.31 WS_ID

Yahoo symbols are projected only for the 79 rows already verified by the v0.32 mapping and OHLCV gate. Provider symbols are not used as identity.

## Collision audit

The stage checks:

- WS_ID collisions against Current Master
- Primary_MIC plus Primary_Ticker collisions
- possible Brazil name and share-class collisions
- existing BR_IBRX100 rows
- duplicate source WS_ID
- duplicate source primary identity

If no collision exists, the planned future row count is:

1,535 plus 98 equals 1,633

If a collision exists, the plan state becomes CONTROLLED_IMPORT_BLOCKED_COLLISIONS, no 1,633 claim is made and the next stage changes to collision remediation.

## Required outputs

The stage writes:

- br_ibrx100_history_gate_v0.33.csv
- br_ibrx100_standard_eligibility_v0.33.csv
- br_ibrx100_standard_eligibility_ready_v0.33.csv
- br_ibrx100_low_liquidity_exception_pool_v0.33.csv
- br_ibrx100_standard_exclusions_v0.33.csv
- br_ibrx100_master_collision_audit_v0.33.csv
- br_ibrx100_controlled_master_import_plan_v0.33.csv
- br_ibrx100_master_import_projection_v0.33.csv
- br_ibrx100_history_cache_v0.33.csv
- eligibility_state_counts_v0.33.csv
- summary_v0.33.json
- stage_checkpoint_v0.33.json
- manifest_v0.33.json

It also writes byte-identical:

- WELT-SWING-CURRENT-Handoff-v0.33.md
- WELT-SWING-CURRENT-Handoff-CURRENT.md

## Result gates

The validator asserts:

- 98 source members
- 79 Strict Ordinary Shares
- exactly 38 unique history-ledger rows
- exactly the standard-liquidity set in history
- zero low-liquidity, liquidity-fail or instrument-fail rows in history
- history PASS only at 260 unique and 252 valid completed bars
- exactly 98 unique import-plan rows
- exactly 98 unique projection rows
- no projection WS_ID duplicates
- no projection Primary_MIC plus Primary_Ticker duplicates
- exact Universe_Master column order
- BVMF, Brazil, BRL and BR_IBRX100 projection constants
- empty Alpha_Symbol
- no guessed ISIN
- unchanged Current Master bytes and 1,535 rows
- unchanged research_partial_1535 bytes
- no import, mutation, eligibility promotion, P0, Sector RS, productive state or Alpha Vantage
- byte-identical v0.33 handoffs

## Next-stage selection

If collision count is zero and the plan is valid:

CURRENT_MASTER_BR_IBRX100_CONTROLLED_SOURCE_SUPERSET_IMPORT_AND_ELIGIBILITY_STATE_MATERIALIZATION

If collision count is greater than zero:

CURRENT_MASTER_BR_IBRX100_IMPORT_COLLISION_REMEDIATION

v0.33 does not start either next stage.
