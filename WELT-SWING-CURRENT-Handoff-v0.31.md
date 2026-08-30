# WELT-SWING LONG DEV — CURRENT HANDOFF

**Version:** v0.31  
**Generated UTC:** 2026-08-30T06:58:03.873879+00:00  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Primary lineage:** `CURRENT_MASTER_CLEAN_RESTART`  
**Trigger/input commit:** `38bb663646ed1bb65180c83d2a403d618f5e49b5`

## 1. Authority

Authoritative DEV master:
`docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Welt-Swing v7.2 remains solely authoritative for productive Swing decisions. Alpha Vantage remains forbidden.

## 2. Current-master universe

Canonical development snapshot remains unchanged at **1,535 securities from 7 of 14 target segments**.

v0.31 performs identity and instrument reconciliation only. No canonical universe mutation occurs.

## 3. Brazil / IBrX 100

Official B3 membership snapshot:
- Official source rows: 98
- Official B3 header date: `2026-08-31`
- Identity PASS via Primary MIC + official ticker + stable WS_ID: 98
- Ordinary-share instrument PASS: 79
- Preferred-share FAIL: 12
- Unit FAIL: 7
- Instrument NOT VERIFIED: 0
- Strict ordinary identity candidates: 79

Primary MIC used: `BVMF`.

The official B3 membership endpoint does not provide ISIN in this response. Under the DEV master identity rule, the fallback identity is therefore:
`Primary MIC + official Primary Ticker + stable WS_ID`.

No ISIN is guessed.

Preferred shares and Units remain official IBrX 100 members but fail the Strict-U3K instrument gate.

## 4. Mexico / S&P-BMV IPC

The official final rebalance document is preserved as a **change ledger only**:
- `VOLAR A` — ADD
- `CUERVO *` — DROP
- announcement: 2026-03-13
- effective: 2026-03-23

This does not prove the complete current IPC membership and therefore does not authorize full-segment import.

## 5. Governance

- Current-master rows before/after: 1,535 / 1,535
- Canonical segments imported in v0.31: 0
- Universe mutation: `false`
- Eligibility promotions: 0
- Liquidity gate: not yet run for Brazil
- Price downloads: `false`
- P0: `false`
- `SWING_U3K_FROZEN`: `false`

## 6. Current checkpoint

- Stage: `CURRENT_MASTER_MATERIALIZED_OFFICIAL_MEMBERSHIP_IDENTITY_RECONCILIATION`
- Run ID: `WS-LONG-CURRENT-MASTER-MEMBERSHIP-IDENTITY-RECONCILIATION-2026-08-30-v0.31`
- Status: `PARTIAL`
- B3 rows checked: 98
- Strict ordinary identity candidates: 79
- Instrument FAIL rows: 19
- Instrument NOT VERIFIED rows: 0
- Output hash: `7c4b8d44b23962f78bb3cef0177b2f2a9c775d9cc8e6695f16a32997a8c62c02`
- Next stage: `CURRENT_MASTER_BR_IBRX100_SOURCE_SEGMENT_FREEZE_AND_LIQUIDITY_PRECHECK`

## 7. Recovery order

1. `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
2. `WELT-SWING-CURRENT-Handoff-CURRENT.md`
3. `output_current_master_membership_identity_reconciliation_v0_31/stage_checkpoint_v0.31.json`
4. `output_current_master_membership_identity_reconciliation_v0_31/manifest_v0.31.json`
5. `output_current_master_membership_identity_reconciliation_v0_31/br_ibrx100_identity_reconciliation_v0.31.csv`
6. `output_current_master_membership_identity_reconciliation_v0_31/br_ibrx100_strict_ordinary_candidates_v0.31.csv`
7. `output_current_master_source_deep_materialization_v0_30/b3_ibrx100_official_raw_v0.30.json`
8. `universe/Welt-Swing-Universe-Master-v2.0.xlsx`

## 8. Handoff policy

Every major DEV stage refreshes both the versioned Current Handoff and `WELT-SWING-CURRENT-Handoff-CURRENT.md`.

## 9. Next stage

`CURRENT_MASTER_BR_IBRX100_SOURCE_SEGMENT_FREEZE_AND_LIQUIDITY_PRECHECK`

Brazil may proceed only as a frozen official-source segment with the reconciled Ordinary-Share subset. Liquidity and data-quality gates remain separate and mandatory.
