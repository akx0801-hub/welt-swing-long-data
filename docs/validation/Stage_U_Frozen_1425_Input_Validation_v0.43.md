# Stage U - Frozen U3K 1425 Input Validation v0.43

## Stage
- Mode: BOUNDED OFFLINE STAGE-U VALIDATION
- Required start HEAD: `7b372ff955b5ff2b8a97e066871cb96290b6c5d8`
- Status: PASS
- P0 was NOT RUN.
- No market-data acquisition.
- No Universe mutation.

## Frozen snapshot identity
- Members: **1425**
- Git blob SHA: `018a03eb4614a197da9d2d566e77f32c61238dad`
- SHA-256: `54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb`
- Hash repeat: PASS
- Frozen file unchanged: PASS

## Membership and eligibility reconciliation
All 1425 Frozen members map exactly to one current v0.39 eligibility row and remain PASS_STRICT_CANDIDATE.

- Missing Frozen -> eligibility mappings: 0
- Unexpected eligible mappings: 0
- Source_WS_ID mismatch: 0
- Primary_MIC mismatch: 0
- Primary_Ticker mismatch: 0
- Fail-closed leakage: 0
- Stage-U exclusions: 0

## Security and instrument validation
- COMMON_STOCK: 1388
- ORDINARY_SHARE: 37
- Incompatible instrument states: 0
- Duplicate Security_Key: 0
- Duplicate Source_WS_ID: 0
- Missing Security_Key / Source_WS_ID / Primary_MIC / Primary_Ticker: 0

## History validation
- HISTORY_OK: 1425
- Minimum History_Observation_Count: 275
- Minimum History_Valid_Observation_Count: 275
- Threshold violations against >=260 unique / >=252 valid: 0

## Liquidity validation
- LIQUIDITY_OK: 1425
- PREFERRED bucket: 1369
- STANDARD bucket: 56
- Minimum Usable20: 20
- Minimum MedianTurnover20_EUR: 15052518.970567
- Standard threshold violations: 0

## Source and market coverage
Evidence cohort:
- AU1: 63
- BASE_1633: 622
- US1: 372
- US2: 368

Primary MIC:
- BVMF: 37
- XASX: 63
- XNAS: 234
- XNSE: 45
- XNYS: 506
- XSHE: 108
- XSHG: 186
- XTAI: 49
- XTKS: 197

Source IDs:
- AU1_EVIDENCE_ADMISSION_GATE: 63
- B3_OFFICIAL_INDEXPROXY_GETPORTFOLIODAY: 37
- SRC_CSI300: 294
- SRC_FTSE_TW50_CW_20260630: 49
- SRC_NIFTY50: 45
- SRC_NIKKEI225: 197
- US1_SP500_COMMON_EVIDENCE_GATE: 372
- US2_SP400_COMMON_ADMISSION: 368

Region: REGION_NOT_VERIFIED.
No direct authoritative region field is present in the v0.39 Stage-U eligibility authority. No broad-region labels were inferred from MIC or source names. Primary_MIC and Source_ID are reported as the persisted market/source coverage.

## SOLS / CTD
- SOLS present: 0
- CTD present: 0

## Stage-U result
P0_INPUT_READY = YES

This means only that the exact Frozen-1425 snapshot is a valid Stage-U input for a future P0 readiness stage. It does not mean P0 occurred and does not authorize scanning or execution.

LONG DEV remains DEV / RESEARCH / SHADOW.
Welt-Swing v7.2 remains the only productive trading authority.
Membership != Eligibility != Scan != Execution.

## Next gate
P0 FROZEN-1425 DATA/CAPABILITY READINESS GATE

Do not execute P0 itself.
