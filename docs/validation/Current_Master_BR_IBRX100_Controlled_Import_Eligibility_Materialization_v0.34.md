# Current Master BR IBrX100 Controlled Import and Eligibility Materialization v0.34

## Stage

- Stage ID: CURRENT_MASTER_BR_IBRX100_CONTROLLED_SOURCE_SUPERSET_IMPORT_AND_ELIGIBILITY_STATE_MATERIALIZATION
- Version: v0.34
- Status: DEV / RESEARCH / SHADOW - NOT PRODUCTIVE
- Lineage: CURRENT_MASTER_CLEAN_RESTART
- Global classification: PARTIAL
- Welt-Swing v7.2 remains the only productive authority.

This stage performs the controlled canonical SOURCE_SUPERSET import of Brazil. It does not run P0, Sector RS, a productive scan, or create SWING_U3K_FROZEN.

## Frozen v0.33 baseline

The workflow pins the current Git blob SHA of every authoritative input. The mandatory starting state is:

| Gate | Required |
|---|---:|
| Current Master rows | 1535 |
| Imported target segments | 7/14 |
| BR source projection | 98 |
| BR strict ordinary | 79 |
| STANDARD_ELIGIBILITY_READY | 38 |
| LOW_LIQUIDITY_EXCEPTION_POOL | 28 |
| STANDARD_U3K_NOT_ELIGIBLE_LIQUIDITY | 13 |
| STANDARD_U3K_NOT_ELIGIBLE_INSTRUMENT | 19 |
| History checked / passed | 38 / 38 |
| Collision count | 0 |
| Scalable status | 98 x SCALABLE_NOT_VERIFIED |
| Provider | YFINANCE_FREE |
| Alpha Vantage | false |

Any mismatch stops the stage before workbook mutation.

## Transactional workbook mutation

The script performs these steps in order:

1. Load the 1535-row canonical workbook and all frozen v0.33 ledgers.
2. Verify workbook sheets and the exact 22-column Universe_Master schema.
3. Read Status_Definitions and require the existing canonical ACTIVE_VERIFIED status. If ambiguous, stop with UNIVERSE_STATUS_SCHEMA_DECISION_REQUIRED.
4. Re-run WS_ID, MIC/ticker, existing-BR and projection-duplicate collision gates.
5. Create universe/snapshots/Welt-Swing-Universe-Master-v2.0-pre-BR-v0.34.xlsx and prove SHA256 and Git-blob identity with the pre-import master.
6. Work only on a temporary workbook copy.
7. Append exactly the 98 projected BR rows, using the existing canonical source/active status.
8. Update Import_Coverage and Run_Summary only after their structures have been recognized unambiguously.
9. Preserve Dedupe_Rules and Status_Definitions.
10. Run all post-import identity, schema, count, coverage and immutability gates on the temporary workbook.
11. Atomically replace the canonical master only after all gates pass.

A failure before the final replacement leaves the canonical master unchanged.

## Master projection semantics

All 98 imported rows must satisfy:

- Country = Brazil
- Primary_Exchange = B3
- Primary_MIC = BVMF
- Primary_Currency = BRL
- Primary_Universe_Index = BR_IBRX100
- Index_Tags contains BR_IBRX100
- Active = true
- Universe_Status = existing canonical ACTIVE_VERIFIED
- Source_ID = B3_OFFICIAL_INDEXPROXY_GETPORTFOLIODAY
- Source_AsOf = 2026-08-31
- Scalable_Tradeability_Status = SCALABLE_NOT_VERIFIED
- Alpha_Symbol empty
- ISIN only if already authoritative; no guessed ISIN
- stable v0.31/v0.33 WS_ID unchanged

Provider symbols are mappings, not security identity.

## Eligibility-state materialization

universe/segments/br_ibrx100_eligibility_state_v0.34.csv contains all 98 source members and exactly:

| Standard eligibility state | Rows |
|---|---:|
| STANDARD_ELIGIBILITY_READY | 38 |
| LOW_LIQUIDITY_EXCEPTION_POOL | 28 |
| STANDARD_U3K_NOT_ELIGIBLE_LIQUIDITY | 13 |
| STANDARD_U3K_NOT_ELIGIBLE_INSTRUMENT | 19 |

For every row:

- Eligibility_State_Materialized_v0_34 = true
- Productive_Eligibility = false
- SWING_U3K_FROZEN_Member = false

The standard-ready snapshot contains exactly 38 rows with Instrument PASS, standard Liquidity PASS, History PASS, and mapping/data-quality PASS.

## Required outputs

The workflow produces the requested audit, summary, checkpoint and manifest files under output_current_master_br_ibrx100_import_v0_34/.

It also produces the byte-identical pre-import workbook backup, the 98-row eligibility state, the 38-row standard-ready snapshot, universe/research_partial_1633.csv, its manifest, and byte-identical versioned/CURRENT handoffs.

The historical universe/research_partial_1535.csv is pinned and must remain unchanged.

## Post-import result gates

A successful stage requires:

- Pre-import master rows = 1535
- Post-import master rows = 1633
- Added BR rows = 98
- Changed preexisting rows = 0
- Unique WS_ID = 1633
- Unique Primary_MIC + Primary_Ticker = 1633
- BR_IBRX100 rows = 98
- Imported target segments = 8
- Missing target segments = 6
- Eligibility state rows = 98
- Standard-ready rows = 38
- research_partial_1633 rows = 1633
- no guessed ISIN
- Alpha_Symbol empty for Brazil
- Scalable status unchanged at SCALABLE_NOT_VERIFIED
- P0 = false
- Sector RS = false
- SWING_U3K_FROZEN = false
- Productive = false
- Alpha Vantage = false
- Source Superset Complete = false
- Stage classification = PARTIAL

## Status flags after success

- Canonical_Master_Import_v0_34 = true
- Universe_Mutated_v0_34 = true
- BR_Source_Superset_Imported_v0_34 = true
- Eligibility_State_Materialized_v0_34 = true
- Productive_Eligibility_Promotion_v0_34 = false

## Next stage

CURRENT_MASTER_REMAINING_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION

The six remaining target segments are US_SP1500, MX_IPC, KR_KOSPI200, AU_ASX200, NZ_NZX50 and ZA_TOP40. v0.35 is not started by this workflow.
