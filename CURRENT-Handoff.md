# WELT-SWING LONG DEV — CURRENT HANDOFF

**Updated:** 2026-08-24 15:32 CEST  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE

## Authority

Authoritative DEV master specification:

`docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Specification: **WELT-SWING LONG DEV v0.1**, frozen 2026-08-23.

Welt-Swing v7.2 remains unchanged and alone productive-authoritative for real Swing decisions until explicit validated promotion.

## Current repo checkpoint

Latest completed technical checkpoint:

**KRX Stock-Kind Instrument Resolution v0.10**

Repo HEAD after v0.10 output commit:

`6f23b314d538b8d7e8bb5d8be68b2b714c714fff`

Commit:

`Resolve KRX stock-kind instruments v0.10`

## Confirmed v0.10 result

- run status: `INSTRUMENT_RESOLUTION_KRX_V0_10_COMPLETE_WITH_SOURCE_BLOCK`
- KRX target rows: **92**
- KRX HTTP status: **400**
- KRX reference rows: **0**
- KRX matched: **0**
- new PASS: **0**
- new FAIL: **0**
- unresolved KR: **92**
- manual-review rows remain: **667**
- strict candidates remain: **2.020**
- strict freeze: **false**
- P0: **false**
- external reference requests: **1**
- no per-security requests
- no price/FX downloads
- Alpha Vantage forbidden
- canonical master unchanged

Remaining segments:

| Segment | Rows |
|---|---:|
| CA_TSX | 105 |
| EU_STOXX600 | 365 |
| HK_HSI | 82 |
| KR_KOSPI200 | 92 |
| MX_IPC | 6 |
| ZA_TOP40 | 17 |
| **Total** | **667** |

## KRX access conclusion

The anonymous KRX Data Marketplace bulk POST remains blocked with HTTP 400.

Current official KRX pages expose login/registration and the official KRX OPEN API requires login plus an approved authentication key. The anonymous route should not be retried repeatedly in the current free/no-credential DEV path.

KR_KOSPI200 remains source-blocked / NOT_VERIFIED until an allowed official bulk route is available.

## Next step

**v0.11 — JSE Equities ISIN Bulk Probe**

Target: **17** remaining `ZA_TOP40` rows.

Official JSE Client Portal exposes an Equities ISIN downloadable-files folder containing `isinfull_e.zip`.

v0.11 is evidence-only:

- max 2 official JSE requests,
- no per-security requests,
- zero eligibility decisions,
- inspect archive structure/fields,
- preserve 667 review rows and 2.020 strict candidates.

If the ZIP is reproducibly obtained and its fields have documented instrument-type semantics, a later v0.12 classifier can be built. Otherwise ZA remains source-blocked.

## Resume rule

1. Read this file.
2. Read the master spec.
3. Read newest `summary_v0.x.json`.
4. Confirm current `main` HEAD.
5. Resume from the smallest valid next stage.

Never regress to an obsolete instrument-resolution workflow.
