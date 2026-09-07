# US-3 Named-Index Tracker Qualification Gate

## Stage decision

**US-3 NAMED-INDEX TRACKER QUALIFICATION GATE — PASS**

**TRACKER QUALIFICATION: PASS**

**R4 QUALIFIED: YES**

**US-3 State After: ACTIVE-EVIDENCE-ONLY**

**BUILD READINESS: BLOCKED**

**NEXT AUTHORIZED STAGE: US-3 Population Evidence Validation Gate v2 — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

This stage qualifies exactly one institutional named-index tracker evidence path. It performs no Admission, no Candidate Population build, no Universe/Research-Partial/Membership write, no final identity/ISIN/listing adjudication, no mapping, history, liquidity, eligibility, Strict/Frozen or Scan/U3K work.

## 1. Start HEAD and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `8288f45ea5eb487394a4c72aefbc59522d07473e`
- origin/main at startcheck: `8288f45ea5eb487394a4c72aefbc59522d07473e`
- Verified predecessor commit: `US-3 population evidence manager gate`
- Authorized stage: **US-3 Named-Index Tracker Qualification Gate — READ-ONLY / EVIDENCE ONLY / NO UNIVERSE WRITE**
- Exactly one tracker path was selected and tested.
- No second tracker/provider path was tested.

Repository references used:

- `docs/spec/US3_Population_Evidence_Manager_Gate.md`
- `docs/spec/US3_Population_Evidence_Validation_Gate.md`
- `docs/spec/US3_Admission_Policy_Gate.md`
- `docs/spec/US2_Admission_Policy_ReadOnly.md`
- `docs/spec/US2_SP400_Admission_Build_Report.md`
- `scripts/us2_sp400_admission_build.py`
- `docs/spec/US1_Integration_Evidence_Gate_Report.md`
- `docs/spec/Post_Integration_Integrity_Audit_US1_US2.md`
- `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

## 2. Governance and current state

WELT-SWING LONG DEV remains **DEV / RESEARCH / SHADOW**. Welt-Swing v7.2 remains the **SOLE PRODUCTIVE AUTHORITY**.

Baseline retained:

| Measure | State |
|---|---:|
| Research Partial | 2527 |
| Strict | 759 |
| Frozen | 0 |
| US-1 | 372 |
| US-2 | 369 |
| US total | 741 |
| AU-1 | 153 |
| Canada | PARKED |
| Korea | PARKED |
| US-3 | ACTIVE-EVIDENCE-ONLY |
| US-3 Population Evidence Validation | FAIL |
| US-3 Build Readiness | BLOCKED |
| Manager Decision | AUTHORIZE ONE TARGETED EVIDENCE PATH |

Alpha Vantage remains prohibited.

## 3. US-2 R4 precedent

US-2 provides the direct methodological precedent. `scripts/us2_sp400_admission_build.py` used iShares IJH S&P MidCap 400 holdings as Rank-4 institutional named-index membership evidence. The architecture required an institutional provider, explicit index relationship, machine-readable Security-level holdings, explicit As-of-Date, identifiers including ticker/ISIN/security name/exchange, reproducible materialization, measurable row count and provenance. The US-2 build report recorded Wiki-only admits = 0.

Only this method was transferred. No US-2 product or endpoint was assumed to apply automatically to US-3.

## 4. Selected single tracker path

Exactly one path was selected:

- Provider: **BlackRock / iShares**
- Product: **iShares Core S&P Small-Cap ETF**
- Ticker: **IJR**
- Official product identifier in source URL: **239774**
- Tracked benchmark: **S&P SmallCap 600 Index**
- Product page: `https://www.ishares.com/us/products/239774/ishares-core-sp-smallcap-etf`
- BlackRock institutional product page: `https://www.blackrock.com/us/financial-professionals/products/239774/`

Selection rationale: same institutional provider family and holdings architecture that proved successful in US-2, explicit exact benchmark identity, official holdings section, downloadable holdings data, current As-of-Date and Security-level identifier fields. This is the highest-methodological-similarity one-path choice available under the manager authorization.

No other tracker was searched or tested after selection.

## 5. Tracking relationship evidence

The official iShares/BlackRock product page identifies the benchmark as:

**S&P SmallCap 600 Index**

This is an exact named-index match, not generic small-cap exposure.

- Institutional Provider: **YES**
- Named-Index Relationship: **PASS**

## 6. Holdings access

The official product page exposes a dedicated Holdings section and an explicit **Download Holdings CSV** control. The holdings view is Security-level, not merely a top-holdings marketing panel.

The current official page reports:

- Number of Holdings: **669**
- As-of-Date: **2026-09-03**

The visible holdings schema includes Security-level rows and fields including ticker, security name/type, sector, asset class, market value/weight, CUSIP, ISIN and SEDOL.

Assessment:

- Holdings Access: **PASS**
- Security-Level Holdings: **PASS**
- Downloadable: **YES**
- Reproducible Access: **YES** at product-page/holdings-control level

This qualification stage does not promote those holdings into Membership and does not create an Admission file.

## 7. As-of-Date and currentness

- Snapshot As-of-Date: **2026-09-03**
- Retrieval Date: **2026-09-07**
- As-of-Date Present: **YES**
- Currentness: **PASS**

The four-day age is suitable for an immediately following evidence-validation stage. A future v2 validation must recheck the As-of-Date before sealing any sidecar.

## 8. Security-level granularity

The holdings presentation is Security-level and exposes individual equity positions rather than issuer aggregates or sector totals only.

**Security-Level Row Quality: PASS**

## 9. Identifier fields

Observed holdings schema:

- Ticker: **YES**
- Security Name: **YES**
- CUSIP: **YES**
- ISIN: **YES**
- Exchange: **not established from the visible holdings schema in this qualification step**
- Other Security Identifier: **SEDOL**

No identifier was synthesized. No CUSIP-to-ISIN conversion was performed.

**Identifier Sufficiency: STRONG**

Ticker + security name + CUSIP + ISIN + SEDOL is sufficient for later reconciliation even if exchange remains to be resolved separately in Admission/Identity stages.

## 10. Completeness

Source-reported holdings count: **669** as of 2026-09-03.

The official page describes the holdings set as the fund holdings and provides a full holdings download control. It also explicitly notes that exchange-traded index futures may be used to offset cash/receivables and separately reports a small Cash and/or Derivatives exposure. Therefore a holdings row count need not equal exactly 600.

Because this qualification stage did not materialize and classify the full CSV row-by-row, the exact split between equity, cash, futures/derivatives and other rows is not sealed here.

Assessment:

- Expected Index Population: approximately 600
- Observed Holdings Rows: 669 (source-reported)
- Observed Equity Security Rows: not sealed in this stage
- Cash Rows: not sealed in this stage
- Futures / Derivative Rows: not sealed in this stage
- Non-Security Rows: not sealed in this stage
- Duplicate Rows: not sealed in this stage
- Usable Security-Level Rows: not sealed in this stage
- Coverage Ratio: not sealed in this stage
- Population Completeness: **CONDITIONAL**

Condition: v2 must materialize the one qualified IJR holdings file and quantify the complete equity/non-equity split, duplicates and usable Security-level membership coverage. The structure is sufficiently complete to qualify the path, but final population completeness remains a v2 validation responsibility.

## 11. Reproducibility

- Access Reproducibility: **YES**
- Materialization Reproducibility: **LIMITED**
- Row-Level Reproducibility: **LIMITED**

Reason: the official product page and Download Holdings CSV route are stable and reproducible, but this qualification stage did not seal a local downloaded holdings file. The immediately following v2 gate must perform that single-path materialization and hash it.

These LIMITED ratings satisfy the R4 qualification threshold defined by the authorized prompt.

## 12. Provenance

- Source Authority: BlackRock / iShares
- Source Rank: R4
- Product: iShares Core S&P Small-Cap ETF
- Ticker: IJR
- Exact Tracked Index: S&P SmallCap 600 Index
- Source Location: official iShares/BlackRock product pages and official Holdings/Download Holdings CSV control
- Retrieval Date: 2026-09-07
- As-of-Date: 2026-09-03
- Evidence Type: institutional named-index tracker Security-level holdings path
- Materialization Method: official holdings-download route; not sealed locally in this qualification stage
- Source-reported Holdings Count: 669
- Identifier Fields: ticker, security name, CUSIP, ISIN, SEDOL; exchange not established from visible schema
- Completeness: CONDITIONAL pending full v2 materialization/classification
- Reproducibility: access YES; materialization/row-level LIMITED pending sealed v2 snapshot

## 13. Snapshot details

No local Evidence Sidecar was created in this qualification stage.

- Holdings Snapshot Created: **NO**
- Holdings Snapshot Path: **NONE**
- Tracker Snapshot SHA256: **NONE**

This is deliberate: the tracker path is qualified here; the next authorized v2 gate is responsible for using only this qualified IJR path, materializing the population evidence sidecar and sealing it with SHA256.

## 14. R4 qualification matrix

| Criterion | Result |
|---|---|
| Institutional Provider | PASS |
| Exact S&P SmallCap 600 Relationship | PASS |
| Security-Level Holdings | PASS |
| As-of-Date Present | PASS |
| Reproducible Access | PASS |
| Materialization Reproducibility | LIMITED |
| Population Completeness | CONDITIONAL |
| Identifier Sufficiency | STRONG |
| Provenance | PASS |

All central R4 qualification thresholds are met.

**R4 QUALIFIED: YES**

**TRACKER QUALIFICATION: PASS**

## 15. Canada/Korea failure-mode control

- Generic Source Hunt Started: **NO**
- Second Tracker Tested: **NO**
- Multiple Provider Loop Started: **NO**
- Manual Security Recovery Started: **NO**

The single selected IJR path passed qualification, so no second tracker/provider/source path was opened.

## 16. Exact next authorized stage

**US-3 Population Evidence Validation Gate v2 — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

That stage may use only the qualified IJR path. It may not introduce another tracker or substitute source. It must materialize and seal the holdings snapshot, quantify completeness and identifiers, and decide final Population Evidence PASS/FAIL. It still may not perform Admission Build or Universe write.

## 17. No-touch confirmation

No Candidate Population was created. No Admission was performed. No Build was started. No Research Partial, Membership, Universe, Strict, Frozen, US-1, US-2, AU-1, Canada or Korea state was changed. No final identity/ISIN/share-class/listing adjudication, mapping, history, liquidity, eligibility or Scan/U3K work was performed.

## 18. Quality gates G0-G17

- G0 Correct origin/main HEAD — PASS
- G1 Correct authorized single-tracker qualification stage — PASS
- G2 Research Partial 2527 verified — PASS
- G3 Strict 759 verified — PASS
- G4 Frozen 0 verified — PASS
- G5 US-3 ACTIVE-EVIDENCE-ONLY recognized — PASS
- G6 Exactly one tracker path selected — PASS
- G7 Institutional provider verified — PASS
- G8 Exact S&P SmallCap 600 tracking relationship verified — PASS
- G9 Security-level holdings evaluated — PASS
- G10 As-of-Date evaluated — PASS
- G11 Identifier Sufficiency evaluated — PASS
- G12 Completeness evaluated — PASS
- G13 Reproducibility evaluated — PASS
- G14 Provenance / SHA256 documented if snapshot created — PASS (snapshot not created; SHA256 NONE)
- G15 Qualification exactly PASS — PASS
- G16 No Universe/Data write — PASS
- G17 No follow-on stage executed — PASS

**G0-G17: PASS**

## 19. Final state

**US-3 NAMED-INDEX TRACKER QUALIFICATION GATE — PASS**

**TRACKER QUALIFICATION: PASS**

**R4 QUALIFIED: YES**

**US-3 State After: ACTIVE-EVIDENCE-ONLY**

**BUILD READINESS: BLOCKED**

**NEXT AUTHORIZED STAGE: US-3 Population Evidence Validation Gate v2 — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

HARD STOP.