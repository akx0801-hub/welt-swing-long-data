# Brazil IBrX 100 B3 InstrumentReport ISIN Qualification Gate

## Stage decision

**BRAZIL IBRX 100 B3 INSTRUMENTREPORT ISIN QUALIFICATION GATE — PASS**

**B3 INSTRUMENTREPORT QUALIFICATION: FAIL**

**BRAZIL STATE AFTER: PARKED**

**BUILD READINESS: BLOCKED**

**NEXT AUTHORIZED STAGE: Post-Brazil Next-Population Manager Gate — READ-ONLY**

This is a one-shot, source-locked evidence qualification stage. It performs no population rematerialization, no candidate generation, no admission, no Research-Partial/Membership/Universe write, no Frozen write, and no mapping/history/liquidity/eligibility/scan work outside the bounded qualification purpose.

## 1. Start HEAD and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `3de0605c91abee9aa6161b5a8e16dd36a165ba91`
- origin/main at startcheck: `3de0605c91abee9aa6161b5a8e16dd36a165ba91`
- Verified predecessor commit: `Brazil IBrX 100 identity ISIN manager gate`
- Authorized stage: **Brazil IBrX 100 B3 InstrumentReport ISIN Qualification Gate — READ-ONLY / EVIDENCE ONLY / NO UNIVERSE WRITE**

Central repository artifacts used include:

- `docs/spec/Brazil_IBrX100_Identity_ISIN_Manager_Gate.md`
- `docs/spec/Brazil_IBrX100_Identity_ISIN_Validation_Gate.md`
- `docs/spec/Brazil_IBrX100_Admission_Policy_Gate.md`
- `docs/spec/Post_US3_Next_Population_Manager_Gate.md`
- `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
- `universe/segments/br_ibrx100_source_frozen_v0.32.csv`
- `universe/segments/br_ibrx100_strict_ordinary_frozen_v0.32.csv`
- `docs/spec/US1_Integration_Evidence_Gate_Report.md`
- `docs/spec/US2_SP400_Admission_Build_Report.md`
- `docs/spec/AU1_Post_Integration_Integrity_Audit.md`
- `docs/spec/US3_Named_Index_Tracker_Qualification_Gate.md`

No second Brazil evidence class was used.

## 2. Baseline

| Measure | State |
|---|---:|
| Research Partial | 2527 |
| Strict | 759 |
| Frozen | 0 |
| US-1 | 372 |
| US-2 | 369 |
| US total | 741 |
| AU-1 | 153 |
| Usable integrated expansion rows | 894 |
| Canada | PARKED |
| Korea | PARKED |
| US-3 | PARKED |
| Brazil before | ACTIVE-EVIDENCE-ONLY |
| Brazil target | IBrX 100 |
| Primary market | B3 |
| Primary MIC | BVMF |
| Population rows | 98 |
| Unique B3 security codes | 98 |
| Population snapshot As-of | 2026-08-31 |
| Ordinary/Common | 79 |
| Instrument-policy-excluded | 19 |
| Eligible identity/ISIN rows | 79 |
| Identity/ISIN validated | 0 |
| Identity validated / ISIN missing | 79 |

## 3. Source lock

The only authorized external evidence path was:

**B3 BVBG.028.02 InstrumentReport**

No CVM, issuer, alternate B3 dataset, registry, provider, broker, screener or security-by-security recovery path was used.

## 4. B3 BVBG.028.02 dataset identity

Existing repository governance already identified the selected path as B3's official `BVBG.028.02 InstrumentReport` security-master / instrument-reference evidence class.

The official B3 current file-layout / daily-bulletin pages confirm:

- dataset family: `BVBG.028.02 Instruments File` / `InstrumentReport`;
- provider/authority: B3;
- role: instrument identification / instrument registration;
- the official catalogue describes the InstrumentReport as being sent by B3 to participants with instrument identification and sent at the opening of the day;
- a current 2026-09-08 InstrumentReport instance is listed on B3's daily file page with last modification `2026-09-08 00:22` local site display.

Assessment:

- Source Authority: PASS
- Dataset Identity: PASS
- Intended Role: security-master / instrument-reference equivalent
- Expected Security-Level Granularity: YES
- Expected ISIN Field: YES, per the already documented repository governance for the BVBG.028.02 schema

## 5. Currentness

The official B3 daily file page listed `BVBG.028.02 Instruments File` as current on 2026-09-08.

Because the raw report bytes could not be materialized, an embedded report-level As-of-Date could not be independently sealed.

- InstrumentReport As-of-Date: NONE
- Retrieval Date: 2026-09-08
- Currentness: PASS at the official availability/listing level, but not sufficient to cure the materialization hard-gate failure.

## 6. Materialization method and result

The qualification attempted only the official B3 InstrumentReport route.

The B3 daily page exposes the file through its `Pesquisa por pregão` download workflow. In the available execution environment, the current InstrumentReport raw artifact could not be retrieved as exact bytes through a reproducible direct download invocation. The source page and file listing were accessible, but the controlled download interface did not yield a sealable raw file in this stage.

No alternate B3 dataset, CVM source, issuer source, provider or second download path was attempted after this failure.

Therefore:

- Raw Snapshot Materialized: NO
- Raw Path: NONE
- Raw SHA256: NONE
- Raw Row Count: 0
- Encoding: NONE
- Schema/Structure from raw: NOT MATERIALIZED

This is a hard qualification failure under the one-shot rule.

## 7. Raw provenance / integrity

Source provenance is official B3 `BVBG.028.02 InstrumentReport` via B3 daily bulletin / search-by-trading-session infrastructure.

However, without the raw bytes:

- no byte-level SHA256 can be produced;
- no immutable raw artifact can be sealed;
- no row count can be independently reproduced;
- no raw XML/file member inventory can be sealed.

Raw-byte integrity requirement: FAIL.

## 8. Schema inventory

Because raw materialization failed, no actual current-file field inventory can be measured from the 2026-09-08 instance.

Repository/governance evidence supports the expected presence of security-level instrument identity and ISIN within BVBG.028.02, but the qualification stage requires empirical validation against the actual materialized current file.

Accordingly:

- ISIN present in documented schema: YES
- B3 Security Code current-file field inventory: NOT MEASURED
- Trading Code current-file field inventory: NOT MEASURED
- Security Name current-file field inventory: NOT MEASURED
- Instrument Type / Share Class current-file field inventory: NOT MEASURED
- Exchange/Market indicator current-file field inventory: NOT MEASURED
- Issuer identifier current-file field inventory: NOT MEASURED

These missing measurements cannot be inferred into a PASS.

## 9. ISIN field assessment

The existing manager/validation governance identifies an ISIN field in the BVBG.028.02 InstrumentReport evidence class.

But no current raw rows were available for actual field-level counts or validation.

- ISIN Field Present: YES at documented-schema level
- Non-empty ISIN Rows: 0 measured
- Syntactically Valid ISIN Rows: 0 measured
- Luhn PASS Rows: 0 measured
- Unique ISINs: 0 measured
- Duplicate ISIN Rows: 0 measured

The zero counts mean **not measurable because raw materialization failed**, not that the official file contains zero ISINs.

## 10. Security-level granularity

The official B3 catalogue defines the InstrumentReport as an instrument-identification file and the existing repository governance classifies it as security-master / instrument-reference evidence.

- Security-Level Granularity: PASS at documented dataset-design level.

However, empirical current-row granularity could not be independently reproduced because the raw file was not materialized.

## 11. B3 security-code / trading-code mapping

Locked population target:

- Population Rows: 98
- Eligible Ordinary/Common Rows: 79
- Instrument-Policy-Excluded Rows: 19

No current InstrumentReport rows were available to execute the deterministic join.

Therefore:

- Exact Security-Code Matches: 0 measured
- Exact Trading-Code Matches: 0 measured
- Ambiguous Matches: 0 measured
- Unmatched Population Rows: 98 for qualification purposes because no current raw matching table was materialized
- Multiple InstrumentReport Rows per Population Row: 0 measured
- Mapping Coverage: 0.00% measurable qualification coverage

No fallback join was attempted.

## 12. Locked 79-row qualification coverage

For the 79 policy-eligible Ordinary/Common rows:

- Exact InstrumentReport Matches: 0 measured
- Rows with Non-empty ISIN: 0 measured
- Rows with Valid ISIN Syntax: 0 measured
- Rows with Luhn PASS: 0 measured
- Rows with Exact Security-Level Match: 0 measured
- Rows with Exact Share-Class Match: 0 measured
- Fully Qualified Rows: 0
- Qualification Coverage: 0.00%

Again, this is a qualification-measurement failure caused by missing materialized raw input, not evidence that the source itself lacks those records.

## 13. Share-class fidelity

The locked population's existing B3 evidence has already established 79 Ordinary/Common, 12 Preferred and 7 Units.

The InstrumentReport current-file side could not be compared because raw materialization failed.

- Share-Class Exact Match: 0 measured
- Share-Class Ambiguous: 0 measured
- Share-Class Conflict: 0 measured
- Share-Class Fidelity: FAIL for qualification purposes because empirical fidelity was not demonstrated.

## 14. Primary BVMF consistency

The locked population retains its already validated BVMF primary-listing context.

The InstrumentReport itself could not be inspected at row level for an explicit exchange/market field in this run.

- Primary BVMF Consistency: NOT EXPLICITLY ENCODED / NOT EMPIRICALLY MEASURED IN CURRENT RAW FILE

No foreign/secondary/depositary substitution was introduced.

## 15. Instrument-type consistency

Expected locked classification:

- Ordinary/Common: 79
- Preferred: 12
- Units: 7
- Other: 0

No current InstrumentReport raw rows were available for comparison.

- Instrument-Type Consistency: FAIL for qualification purposes because current-file consistency could not be empirically measured.

## 16. Duplicate analysis

No current raw dataset was materialized. Therefore duplicate diagnostics are not evidence-bearing.

- Duplicate Security Codes: 0 measured
- Duplicate Trading Codes: 0 measured
- Duplicate ISINs: 0 measured
- One Population Row -> Multiple InstrumentReport Rows: 0 measured
- Multiple Population Rows -> Same ISIN: 0 measured
- Ambiguous Share-Class Mappings: 0 measured

These are non-observations, not proven absence of duplicates.

## 17. Corporate-action signals

No row-level current InstrumentReport comparison was possible, so no corporate-action mismatch could be diagnosed from this source path.

No recovery or successor mapping was attempted.

## 18. Identifier sufficiency

Documented dataset design is promising, but current-file qualification evidence is insufficient because no deterministic row-level join or ISIN validation could be executed.

**Identifier Sufficiency: WEAK for qualification result.**

This does not reverse the earlier conclusion that the evidence class is conceptually strong; it records that operational qualification failed.

## 19. Materialization reproducibility

**Materialization Reproducibility: FAIL.**

The official B3 file was visible as current, but exact raw bytes could not be reproducibly materialized and sealed in the available execution path.

Under the stage rules, one-time visual/source availability is not enough.

## 20. Row-level reproducibility

**Row-Level Reproducibility: FAIL.**

Without raw materialization, an independent rerun cannot reproduce matched rows, ISINs, share-class mappings, unmatched rows or coverage counts from a sealed input.

## 21. Batch capability

The B3 InstrumentReport is conceptually a batch dataset, but batch processing of the locked 79 rows was not operationally demonstrated in this gate.

**Batch Capability: FAIL for qualification.**

The reason is failed materialization, not a decision that the dataset architecture itself is issuer-by-issuer.

## 22. Manual recovery assessment

Continuing after the failed one-shot path would require either another source/download route or security-by-security recovery, both prohibited.

- Manual Recovery Required: HIGH if Brazil were forced forward after this gate
- Second Source Required: YES to continue despite the failed qualified path; therefore continuation is forbidden

## 23. Failure-mode assessment

- Canada Failure-Mode Risk: LOW inside this gate because no per-security recovery was started; HIGH if continuation were forced after failure.
- Korea Failure-Mode Risk: LOW for population/listing/class architecture, but irrelevant once raw qualification fails.
- US-3 Failure-Mode Risk: HIGH and realized in the decisive form: a methodically credible evidence path could not be operationally materialized/reproduced.

The one-shot stop rule is therefore applied.

## 24. Qualification evidence sidecar

No sidecar was created because there was no current raw InstrumentReport dataset from which to produce deterministic evidence rows.

- Qualification Evidence Sidecar Created: NO
- Qualification Evidence Sidecar Path: NONE
- Qualification Evidence Sidecar SHA256: NONE

No artificial zero-content evidence file is committed.

## 25. Qualification result

**B3 INSTRUMENTREPORT QUALIFICATION: FAIL**

Hard-gate failures:

1. Raw Materialization: FAIL
2. Raw SHA256: absent
3. Materialization Reproducibility: FAIL
4. Row-Level Reproducibility: FAIL
5. Deterministic B3-code/ticker mapping: not executable
6. Share-Class Fidelity: not empirically demonstrated
7. 79-row Coverage: not meaningfully measurable beyond 0 qualified rows
8. Batch Capability: not operationally demonstrated

The source authority and dataset identity themselves pass, but the qualification requires operational reproducibility, not theoretical suitability.

## 26. Brazil state after

**Brazil State After: PARKED**

No second Brazil ISIN evidence path is authorized.

## 27. Build readiness

**BUILD READINESS: BLOCKED**

The Brazil Admission Build remains prohibited.

## 28. Exact next authorized stage

**Post-Brazil Next-Population Manager Gate — READ-ONLY**

Brazil may not be automatically reactivated by that next manager stage.

## 29. No-touch confirmation

No change was made to Research Partial, Membership, Universe, Strict, Frozen, US-1, US-2, US-3, AU-1, Canada, Korea, the 98-row Brazil population snapshot, Mapping, History, Liquidity, Eligibility, Scan/U3K or productive Welt-Swing v7.2.

No candidate population, admission artifact or population refresh was created.

## 30. Quality gates G0-G17

- G0 Correct origin/main HEAD — PASS
- G1 Correct B3 InstrumentReport Qualification stage — PASS
- G2 Research Partial 2527 verified — PASS
- G3 Strict 759 verified — PASS
- G4 Frozen 0 verified — PASS
- G5 Canada/Korea/US-3 remain PARKED — PASS
- G6 Locked existing 98-row IBrX population used — PASS
- G7 No population rematerialization — PASS
- G8 Only B3 BVBG.028.02 path used — PASS
- G9 Raw materialization/reproducibility assessed — PASS, result FAIL
- G10 ISIN field and syntax/Luhn assessed — PASS, documented field exists; zero current rows measurable because raw failed
- G11 Deterministic B3-code/ticker mapping assessed — PASS, not executable because raw failed; qualification fails closed
- G12 Share-class fidelity assessed — PASS, result FAIL for lack of current raw comparison
- G13 79-row eligible coverage measured — PASS, 0/79 fully qualified because no raw mapping could be executed
- G14 Batch/manual-recovery risk assessed — PASS
- G15 Qualification exactly FAIL — PASS
- G16 No universe/membership/research-partial write — PASS
- G17 No follow-on stage executed — PASS

**G0-G17: PASS**

## 31. Final state

**STAGE STATUS: PASS**

**B3 INSTRUMENTREPORT QUALIFICATION: FAIL**

**BRAZIL STATE AFTER: PARKED**

**BUILD READINESS: BLOCKED**

**NEXT AUTHORIZED STAGE: Post-Brazil Next-Population Manager Gate — READ-ONLY**

HARD STOP.
