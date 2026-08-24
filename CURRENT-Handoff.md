# WELT-SWING LONG DEV — CURRENT HANDOFF

**Updated:** 2026-08-24 16:24 CEST  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE

## Authority
Authoritative DEV master specification: `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Welt-Swing v7.2 remains unchanged and alone productive-authoritative.

## Current checkpoint
Latest completed technical checkpoint: **JSE Instrument Resolution v0.12**

Repo HEAD: `e4356be2336630c7f0dafa73d99ffa60dbcd4df8`

Confirmed v0.12:
- JSE reference rows: **14,589**
- ZA targets: **17**
- exact matches: **17**
- PASS: **17**
- FAIL: **0**
- unresolved ZA: **0**
- record layout validated: **true**
- remaining manual rows: **650**
- strict candidates: **2,037**
- strict freeze: **false**
- P0: **false**
- Alpha Vantage forbidden

Remaining:
- CA_TSX 105
- EU_STOXX600 365
- HK_HSI 82
- KR_KOSPI200 92
- MX_IPC 6

## Next step
**v0.13 — TMX Symbol Semantics Probe**

Evidence-only for Canada:
- max 3 official TMX requests
- no per-security requests
- current bulk symbol confirmation
- suffix-pattern distribution for the 105 frozen targets
- capture formal TMX suffix semantics if accessible
- zero eligibility decisions
- preserve 650 review rows and 2,037 strict candidates

A later v0.14 classifier is allowed only if official evidence deterministically separates common/ordinary shares from units/preferreds/other structures.

## Resume rule
Read this file, then the master spec, then newest summary, confirm `main` HEAD, resume from the smallest valid next stage.
