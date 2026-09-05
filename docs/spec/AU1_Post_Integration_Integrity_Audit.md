# AU-1 Post-Integration Integrity Audit

## Scope

Repository: `akx0801-hub/welt-swing-long-data`
Branch: `main`
Audit mode: read-only verification of the completed AU-1 controlled integration write. No AU-1 write rerun, no universe repair, no additional population, and no next-stage activity.

## Commit lineage

- Audit start HEAD: `18d1d46af9179cd18a47ac002899e6a052d22df8`
- Write HEAD / baseline parent: `f6e351170c24cabe9e0531abe76707f5b1e95f43`
- Write commit: `AU-1 controlled integration write 153 sealed INTEGRATION_READY no review no nws`
- Parent/baseline Research Partial: 2,374 data rows (2,375 lines including header)
- Post-write Research Partial: 2,527 data rows (2,528 lines including header)
- Commit diff: 153 additions and 0 deletions for the Research Partial file

## Integrity results

| Check | Expected | Actual | Result |
|---|---:|---:|---|
| Research Partial | 2,527 | 2,527 | PASS |
| Arithmetic | 2,374 + 153 | 2,527 | PASS |
| AU-1 integration | 153 | 153 | PASS |
| Missing | 0 | 0 | PASS |
| Extra | 0 | 0 | PASS |
| Prefix FIELD_DIFF | 0 | 0 | PASS |
| WS_ID duplicates | 0 | 0 | PASS |
| Non-empty ISIN duplicates | 0 | 0 | PASS |
| Full identity duplicates | 0 | 0 | PASS |
| Identity conflicts | 0 | 0 | PASS |
| Review/Exclude written | 0 | 0 | PASS |
| Provenance | AU1_EVIDENCE_ADMISSION_GATE | AU1_EVIDENCE_ADMISSION_GATE | PASS |
| Sealed source SHA256 prefix | 2921df416aeb33dd | 2921df416aeb33dd | PASS |

All 153 AU-1 rows carry valid ISIN, XASX as Primary_MIC, a Primary_Ticker, and a WS_ID. No identity collision with the 2,374-row baseline was found. Ticker-only overlap across different MICs is not treated as an identity collision.

## Exclusion QA

The following were not written:

- PDIDB
- SGH
- VAU
- DNL
- ELV
- NWS
- ISIN `AU000000NWS2`

No Build-REVIEW or Build-EXCLUDE rows were written.

## No-touch QA

Verified unchanged:

- Strict = 759
- Frozen = 0
- US-1 = 372
- US-2 = 369
- Welt-Swing v7.2
- History
- Liquidity
- Eligibility
- Scan/U3K

The local sealed input `output_au1_evidence_gate/AU1_INTEGRATION_READY.csv` was not reconstructed and is not claimed to exist on origin.

## Gates

- G0 Correct HEAD — PASS
- G1 Correct baseline — PASS
- G2 Research Partial count — PASS
- G3 Exact AU-1 count — PASS
- G4 Prefix integrity — PASS
- G5 Missing = 0 — PASS
- G6 Extra = 0 — PASS
- G7 WS_ID uniqueness — PASS
- G8 ISIN uniqueness — PASS
- G9 Full identity uniqueness — PASS
- G10 Identity conflict = 0 — PASS
- G11 Review/Exclude = 0 — PASS
- G12 Five Identity Review rows absent — PASS
- G13 NWS absent — PASS
- G14 Provenance correct — PASS
- G15 Strict/Frozen unchanged — PASS
- G16 US-1/US-2 unchanged — PASS
- G17 No unrelated changes — PASS

## Decision

**AU-1 POST-INTEGRATION AUDIT — PASS**

Next step: none in this audit. HARD STOP.
