# WELT-SWING LONG DEV — CURRENT HANDOFF

**Version:** v0.28  
**Generated UTC:** 2026-08-29T10:03:08.927209+00:00  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Primary lineage:** `CURRENT_MASTER_CLEAN_RESTART`  
**Trigger/input commit:** `a804e0ab3e3e5e960390d6b30c39e3184dd1b5c2`

## 1. Authority

Authoritative DEV master:

`docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Welt-Swing v7.2 remains unchanged and solely authoritative for productive Swing decisions.

Alpha Vantage remains forbidden.

## 2. Current primary universe truth

The current-master r6 clean-restart snapshot contains **1535 securities from 7 of 14 target segments**.

It is a valid **RESEARCH_PARTIAL source snapshot**, not the final global SOURCE_SUPERSET and not a `SWING_U3K_FROZEN`.

Imported current-master segments:

- `EU_STOXX600` — STOXX Europe 600: 600 rows
- `CA_TSX` — S&P/TSX Composite: 217 rows
- `JP_N225` — Nikkei 225: 225 rows
- `HK_HSI` — Hang Seng Index: 93 rows
- `CN_CSI300` — CSI 300: 300 rows
- `IN_NIFTY50` — Nifty 50: 50 rows
- `TW_TW50` — FTSE TWSE Taiwan 50: 50 rows

Missing target segments:

- `US_SP1500` — S&P Composite 1500: `SOURCE_BLOCKED_FULL_EXPORT_LOGIN_REQUIRED`
- `MX_IPC` — S&P/BMV IPC: `NOT_IMPORTED_OFFICIAL_FULL_SOURCE_NOT_MATERIALIZED`
- `KR_KOSPI200` — KOSPI 200: `NOT_IMPORTED_OFFICIAL_FULL_SOURCE_NOT_MATERIALIZED`
- `AU_ASX200` — S&P/ASX 200: `NOT_IMPORTED_OFFICIAL_FULL_SOURCE_NOT_MATERIALIZED`
- `NZ_NZX50` — S&P/NZX 50: `NOT_IMPORTED_OFFICIAL_FULL_SOURCE_NOT_MATERIALIZED`
- `BR_IBRX100` — IBrX 100: `NOT_IMPORTED_OFFICIAL_FULL_SOURCE_NOT_MATERIALIZED`
- `ZA_TOP40` — FTSE/JSE Top 40: `NOT_IMPORTED_OFFICIAL_FULL_SOURCE_NOT_MATERIALIZED`

## 3. Identity state

- Current-master rows: 1535
- Unique WS_ID: 1535
- Duplicate WS_ID rows: 0
- Strict ISIN + MIC + Primary Ticker rows: 97
- Allowed fallback MIC + Primary Ticker + WS_ID rows: 1438
- Incomplete/invalid identity rows: 0

## 4. Historical r6 price snapshot — context only

The frozen historical `output_research_1535/coverage.json` is dated `2026-08-23T20:31:19.162779+00:00` and is **not a fresh current price run**.

- Universe: 1535
- READY: 1287
- Mapping coverage: 99.9349%
- Price-ready coverage: 83.8436%
- P0: `NOT_RUN_PARAMETERS_NOT_YET_PROMOTED`

Do not use this historical coverage file as proof that prices are currently fresh.

Research-snapshot identity reconciliation:

- Authoritative side: `CURRENT_MASTER_XLSX`
- Exact identity-key matches: 1534
- Drift rows recorded: 1
- Only in current master: 0
- Only in research snapshot: 0
- Current master blocked by historical snapshot drift: `false`

Any drift is documented in `research_snapshot_identity_drift_v0.28.csv`; it does not override the current XLSX.

## 5. Legacy lineage closeout

v0.27 successfully closed the useful legacy/pre-master requalification loop.

The old Phase2/3663 lineage remains engineering/diagnostic evidence only and is **not canonical source authority under the current master**.

Legacy v0.27 did not change instrument decisions or eligibility and did not run P0.

## 6. Current v0.28 checkpoint

- Stage: `CURRENT_MASTER_OFFICIAL_SOURCE_UNIVERSE_RECONCILIATION_AND_FREEZE_PLAN`
- Run ID: `WS-LONG-CURRENT-MASTER-UNIVERSE-RECONCILIATION-2026-08-29-v0.28-r3`
- Status: `PARTIAL`
- Input count: 14
- Checked: 14
- PASS accounting: 7
- FAIL accounting: 7
- Core output hash: `f5e9ae5b799d16ad158e061bc1989b98f00d683ddb90afd16dafe85ec9b2a0be`
- Coverage gate: `BLOCKED_CURRENT_MASTER_SOURCE_SUPERSET_INCOMPLETE_7_OF_14`
- Strict U3K frozen: `false`
- P0 run: `false`

## 7. Recovery order

For reconstruction after context loss, use this order:

1. `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
2. `WELT-SWING-CURRENT-Handoff-CURRENT.md`
3. `output_current_master_reconciliation_v0_28/stage_checkpoint_v0.28.json`
4. `output_current_master_reconciliation_v0_28/manifest_v0.28.json`
5. `universe/Welt-Swing-Universe-Master-v2.0.xlsx`
6. `universe/research_partial_1535_manifest.json`
7. `output_research_1535/coverage.json` only as historical price-context
8. `output_official_security_type_data_requalification_v0_27/summary_v0.27.json` only for legacy closeout

Never reconstruct current-master canonical membership from the legacy Phase2/3663 source superset.

## 8. Frozen input SHA-256

- DEV master: `aa9ed6f7d4797cb8061f9496043cb9901cb454712b1206750514b284b5600355`
- Current master r6 XLSX: `bfef93b8a3abbc5f641a5db52b17c10f36455add748b66c55d907d027caaecba`
- Research 1535 CSV: `f590eeeb60962aea5e688cde0877dc61fda37066df22e9f75748ac187cafaf3c`
- Research 1535 manifest: `fdec8b407a8411585ed76c02cf4236b0e86f22c14ee4e415cecc4cd5995907eb`
- Historical research coverage: `dc1e10da129fa96e8db300f74f077fcfb521b8c5d5eb41b79efb28da495aa54a`
- Legacy v0.27 summary: `4a0ce2759bef1ca4e1a076d982e7d331988cd8a35a9a52d1db8207eb86215190`
- Legacy v0.27 checkpoint: `0c7b242b073fc078c5afa92bbc9a9da912ab57b499870f8a590660a993c64f77`

## 9. Next stage

`CURRENT_MASTER_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION`

Primary goal: materialize/freeze official source provenance for the current-master lineage and acquire the missing official full constituent sources without third-party substitution.

## 10. Handoff policy

From v0.28 onward, major development stages should refresh both:

- a versioned handoff (`WELT-SWING-CURRENT-Handoff-vX.Y.md`)
- the stable recovery alias (`WELT-SWING-CURRENT-Handoff-CURRENT.md`)

The stable alias is the first recovery document after the DEV master.
