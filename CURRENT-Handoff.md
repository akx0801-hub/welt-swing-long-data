# WELT-SWING LONG DEV — CURRENT HANDOFF

**Updated:** 2026-08-24 18:32 CEST  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE

## Authority

Authoritative DEV master specification:
`docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Welt-Swing v7.2 remains the sole productive Swing authority until explicit validated promotion.

## Latest completed checkpoint

**S&P/TSX Semantics Remediation v0.15**

Repo HEAD after v0.15 output commit:
`b6ff0bacce934ff108293b330d91dba46a39be66`

v0.15 result:
- run status: `SP_TSX_SEMANTICS_REMEDIATION_V0_15_COMPLETE_WITH_SOURCE_BLOCK`
- public S&P methodology article: HTTP 403 in GitHub runner
- localized official S&P methodology PDF: HTTP 403
- Canada decisions: 0
- remaining manual rows: 650
- strict candidates: 2,037
- strict freeze: false
- P0: false
- Alpha Vantage forbidden

## Current unresolved instrument segments

- EU_STOXX600: 365
- CA_TSX: 105
- KR_KOSPI200: 92
- HK_HSI: 82
- MX_IPC: 6
- total: 650

The source circuit-breaker principle now applies to repeated S&P/TSX access attempts in this development path. Do not keep retrying equivalent blocked URLs without a materially different approved route.

## Next step

**v0.16 — RESEARCH_PARTIAL Snapshot Freeze**

Reason:
The master spec explicitly permits `RESEARCH_PARTIAL` when a valid full Strict Universe is not available, provided coverage is explicit.

v0.16 does NOT create `SWING_U3K_FROZEN`.

It freezes only the currently verified strict subset:
- full eligibility rows: 3,657
- included verified strict rows: 2,037
- instrument-unresolved excluded rows: 650
- other non-strict rows: 970

P0 is not run in v0.16.

After v0.16, the next stage is:
`P0_RESEARCH_PARTIAL_PARAMETER_FREEZE_AND_DRY_RUN`.

Any later candidate claim must be limited to the verified coverage and must never be presented as the globally best candidate.

## Resume rule

1. Read this file.
2. Read the master spec.
3. Read the newest summary and stage checkpoint.
4. Confirm `main` HEAD.
5. Resume from the smallest valid stage.


## v0.16 Fix 1

Der erste v0.16-Run erreichte die Frozen-Input-Gates erfolgreich und scheiterte am Count-Gate:

`Full eligibility rows 3657 != expected 3663`

Korrigierte Ebenentrennung:
- Raw Price Universe: **3.663**
- konsumierte Instrument-/Eligibility-Tabelle: **3.657**
- Verified Strict: **2.037**
- Instrument Unresolved: **650**
- Other Non-Strict: **970**

Keine Änderung an Frozen-Input-Blobs, Eligibility-Regeln, Alpha-Vantage-Verbot, P0-Status oder produktiver Authority.
