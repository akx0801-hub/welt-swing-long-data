# WELT-SWING LONG DEV — CURRENT HANDOFF

**Updated:** 2026-08-24 14:39 CEST  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE

## 1. Authoritative specification

Authoritative DEV master specification:

`docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Secured original DOCX currently present in the repository:

`docs/spec/Welt-Swing-Long-DEV-v0.1-2026-08-23-1.docx`

Specification version: **WELT-SWING LONG DEV v0.1**  
Specification freeze date: **2026-08-23**

Rules:
- Read the master specification before continuing development.
- Do not reconstruct the specification from memory when the source artifact is available.
- Do not silently modify v0.1; material rule changes require a new spec version plus validation/promotion.
- Repo implementation versions such as v0.8/v0.9/v0.10 are not prompt/specification versions.
- Welt-Swing v7.2 remains unchanged and alone productive-authoritative for real Swing decisions until explicit later promotion.
- `ALPHA_VANTAGE_ALLOWED = FALSE`.

## 2. Current repository checkpoint

Repository: `akx0801-hub/welt-swing-long-data`  
Branch: `main`  
Current HEAD: `0a73453a34a65f6fa5167b25d3c2a3e30dc615a4`  
Commit: `Probe six primary-market reference sources v0.9`

Latest completed technical checkpoint:

**Primary-Market Bundle Probe v0.9**

Authoritative v0.9 evidence:
- `docs/validation/Instrument_Resolution_Primary_Bundle_v0.9.md`
- `output_instrument_resolution_v0_9/summary_v0.9.json`
- `output_instrument_resolution_v0_9/source_probe_status_v0.9.csv`
- `output_instrument_resolution_v0_9/hkex_reference_matches_v0.9.csv`
- `output_instrument_resolution_v0_9/krx_reference_matches_v0.9.csv`
- `output_instrument_resolution_v0_9/discovered_bulk_links_v0.9.csv`

## 3. Confirmed v0.9 result

Run status:

`PRIMARY_MARKET_BUNDLE_PROBE_V0_9_COMPLETE`

Frozen invariants preserved:
- source manual rows from v0.8: **667**
- remaining manual rows v0.9: **667**
- strict candidates v0.8: **2,020**
- strict candidates v0.9: **2,020**
- decisions changed: **0**
- strict freeze allowed: **false**
- P0 run: **false**
- productive trading authority: **false**
- Alpha Vantage allowed: **false**
- price downloads performed: **false**
- FX downloads performed: **false**
- per-security web calls: **false**
- canonical master mutated: **false**

Request governance:
- markets probed: **6**
- external reference requests: **6**
- configured maximum: **6**
- request bound respected: **true**

Remaining review queue:
- CA_TSX: **105**
- EU_STOXX600: **365**
- HK_HSI: **82**
- KR_KOSPI200: **92**
- MX_IPC: **6**
- ZA_TOP40: **17**
- total: **667**

## 4. Source-by-source v0.9 evidence

### Hong Kong / HKEX — usable evidence acquired

Official HKEX Full List of Securities:
- HTTP 200
- XLSX parsed successfully
- reference rows: **17,825**
- HSI target rows: **82**
- matched rows: **82**
- coverage: **100%**

Important classification boundary:
- HKEX `Category = Equity` / `Sub-Category = Equity Securities (Main Board)` is not by itself sufficient to prove ordinary/common share, because HKEX officially defines equity securities as including both ordinary and preference shares.
- Therefore v0.9 correctly made no PASS decision from this field alone.

### Korea / KRX — request route needs remediation

Official KRX Data Marketplace bulk POST:
- target rows: **92**
- HTTP status: **400**
- parse not attempted
- no KRX rows matched in v0.9

The intended KRX base-information dataset remains relevant because KRX stock basic information exposes security-group and stock-kind fields such as `SECUGRP_NM` and `KIND_STKCERT_TP_NM`; the latter is the stock-kind field required for deterministic common/preferred classification once the official bulk route is successfully retrieved.

### Canada / TSX — official page reachable, classification evidence not yet materialised

- HTTP 200
- HTML capability probe succeeded
- official page contains a full-list download route, but v0.9 did not yet obtain a security-type field sufficient for strict common/ordinary classification.

### Europe / STOXX Europe 600 — runner TLS problem

- GitHub Actions request failed before content parsing
- SSL certificate verification error
- no classification inference made
- official STOXX page still exposes component/reference-data sections, so the next route should remediate transport/access rather than weaken source governance.

### Mexico / BMV — page reachable, issuer-level evidence only

- HTTP 200
- HTML probe succeeded
- BMV issuer pages distinguish instruments/series and descriptions, including equity shares and certificate structures such as CPO, but v0.9 correctly did not infer strict eligibility from issuer membership alone.

### South Africa / JSE — reference-data semantics found, live bulk file not yet acquired

- HTTP 200
- HTML probe succeeded
- 21 candidate bulk/reference links discovered across MX/ZA
- JSE reference-data documentation defines `InstrumentsEquity.csv` and instrument-type semantics; however a current free public bulk file sufficient for the 17 targets has not yet been materialised.

## 5. Why Strict U3K and P0 remain blocked

The master specification requires `Instrument_Type = UNKNOWN` to remain non-PASS in the Strict Universe.

Therefore:
- no strict U3K freeze yet,
- no complete global P0 claim,
- no productive trade authority.

The current strict candidate count remains **2,020** until deterministic evidence changes it.

## 6. Next DEV step — v0.10

v0.10 should be a **bounded deterministic remediation/classification stage**, not a broad web search.

Priority order:

1. **KRX route remediation**
   - acquire one official KOSPI stock-basic-information bulk payload using the correct browser/session/referer request pattern;
   - capture `ISU_SRT_CD`, `SECUGRP_NM`, `KIND_STKCERT_TP_NM`;
   - exact-match the 92 frozen KOSPI200 target codes;
   - classify only rows whose official stock-kind field unambiguously means common/ordinary vs preferred/non-standard.

2. **STOXX transport remediation**
   - resolve GitHub-runner certificate/access problem for the official STOXX component/reference-data route;
   - no third-party constituent substitution.

3. **HKEX semantic refinement**
   - retain the verified 82/82 match;
   - seek an official security-type discriminator beyond generic `Equity`, or leave unresolved.

4. **TMX/BMV/JSE bulk-source refinement**
   - follow only official bulk/reference routes;
   - no per-security loop where a bulk source is reasonably available;
   - no name-based or index-membership-only PASS.

v0.10 may change eligibility only where official security-specific fields with documented semantics are present. All other rows remain review/NOT_VERIFIED.

## 7. Resume rule

For a new chat/session:
1. Read this `CURRENT-Handoff.md`.
2. Read the authoritative master spec in `docs/spec/`.
3. Read the newest repo summary/output.
4. Confirm current `main` HEAD.
5. Resume from the smallest valid next stage.

Older handoffs are provenance only when superseded by a newer repo checkpoint.

## 8. Productive boundary

All repository v0.x work remains DEV / SHADOW.

A DEV result does not authorize a real trade. Welt-Swing v7.2 remains the productive authority until explicit validated promotion.
