# WELT-SWING LONG DEV — CURRENT HANDOFF

**Updated:** 2026-08-24 15:07 CEST  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE

## Authority

Authoritative DEV master specification:

`docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Specification: **WELT-SWING LONG DEV v0.1**, frozen 2026-08-23.

Welt-Swing v7.2 remains unchanged and alone productive-authoritative for real Swing decisions until explicit validated promotion.

## Current repo checkpoint

Latest completed technical checkpoint: **Primary-Market Bundle Probe v0.9**

Confirmed v0.9 state:

- run status: `PRIMARY_MARKET_BUNDLE_PROBE_V0_9_COMPLETE`
- manual-review rows: **667**
- strict candidates: **2.020**
- strict freeze: **false**
- P0: **false**
- six official/bourse-level requests, request bound respected
- decisions changed: **0**
- HKEX: **82/82 exact matches**
- KRX: HTTP 400 source block
- CA/MX/ZA: official pages reachable, no strict security-type inference yet
- EU/STOXX: TLS/certificate failure in GitHub runner
- Alpha Vantage: forbidden

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

## Next step

**v0.10 — KRX Stock-Kind Instrument Resolution**

Goal: remediate the KRX request and deterministically classify only the 92 frozen KOSPI200 target rows from official `SECUGRP_NM` and `KIND_STKCERT_TP_NM`.

Strict PASS only for exact KRX code match + `주권` + `보통주`.

Preferred labels containing `우선주` are strict FAIL.

Everything else remains NOT_VERIFIED.

No per-security requests. One official KRX bulk POST maximum. If source access remains blocked, zero new decisions and the run completes fail-closed.

## Resume rule

1. Read this file.
2. Read the master spec.
3. Read the newest `summary_v0.x.json`.
4. Confirm `main` HEAD.
5. Resume from the smallest valid next stage.

No obsolete workflow may be run to regress the frozen state.
