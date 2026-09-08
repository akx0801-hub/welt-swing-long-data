# Brazil IBrX 100 Identity / ISIN Validation Gate

## Stage decision

**BRAZIL IBRX 100 IDENTITY / ISIN VALIDATION GATE — PASS**

**BUILD READINESS: BLOCKED**

**NEXT AUTHORIZED STAGE: Brazil IBrX 100 Identity/ISIN Manager Gate — READ-ONLY**

This is a read-only / sidecar-only evidence gate. It performs no population rematerialization, no candidate build, no admission, no Research-Partial/Membership/Universe write, no Frozen write, no mapping/history/liquidity/eligibility/scan work and no productive Welt-Swing v7.2 change.

## 1. Start HEAD and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `b284a0dfc888460a9ac373f53f73849eedff6996`
- origin/main at startcheck: `b284a0dfc888460a9ac373f53f73849eedff6996`
- Verified predecessor commit: `Brazil IBrX 100 admission policy gate`
- Authorized stage: **Brazil IBrX 100 Identity/ISIN Validation Gate — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

Central repository artifacts actually used include:

- `docs/spec/Brazil_IBrX100_Admission_Policy_Gate.md`
- `docs/spec/Post_US3_Next_Population_Manager_Gate.md`
- `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
- `universe/segments/br_ibrx100_source_frozen_v0.32.csv`
- `universe/segments/br_ibrx100_strict_ordinary_frozen_v0.32.csv`
- `docs/validation/Current_Master_Materialized_Official_Membership_Identity_Reconciliation_v0.31.md`
- `docs/validation/Current_Master_BR_IBRX100_Source_Segment_Freeze_Liquidity_Precheck_v0.32.md`
- `docs/validation/Current_Master_BR_IBRX100_Controlled_Import_Eligibility_Materialization_v0.34.md`
- `output_current_master_br_ibrx100_import_v0_34/br_ibrx100_imported_rows_v0.34.csv`
- `universe/research_partial_1633.csv`
- relevant prior US/AU/Canada/Korea identity/evidence policy artifacts already referenced by the preceding policy gate.

External method check was limited to official B3 evidence architecture only. No generic per-security source hunt was started.

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
| Brazil target | IBrX 100 |
| Primary market | B3 |
| Primary MIC | BVMF |
| Population evidence | PASS |
| Population rows | 98 |
| Unique B3 security codes | 98 |
| Population snapshot As-of-Date | 2026-08-31 |
| Build readiness before stage | READY WITH CONDITIONS |

## 3. Population lock

The sole input population is exactly the already materialized and frozen 98-row official B3 IBrX 100 security-level snapshot.

No constituent source was refreshed. No all-B3, Ibovespa, BDR/ADR, secondary-listing or other Brazil population was introduced.

**Population Rematerialized: NO.**

## 4. Policy lock

The preceding policy gate is retained unchanged:

- Ordinary/Common: POTENTIALLY ADMIT
- Preferred: EXCLUDE
- Units: EXCLUDE
- ETF/Fund: EXCLUDE
- BDR: EXCLUDE
- ADR/DR: EXCLUDE
- Rights/Warrants: EXCLUDE
- Structured/Debt: EXCLUDE
- Foreign Secondary Listings: EXCLUDE
- Unknown Instrument: REVIEW

No instrument policy was renegotiated.

## 5. Evidence hierarchy and bounded method

The stage applied the required fail-closed hierarchy:

1. existing repository B3 evidence;
2. one primary authoritative B3 identity/ISIN evidence class;
3. at most one qualified secondary cross-check if required.

The decisive repository fact is that the official B3 IBrX 100 population lineage provides exact B3 trading code, security name, B3 type, BVMF primary MIC and security-level membership, but explicitly records `Official_Source_Provides_ISIN = False` and leaves ISIN blank.

The official B3 architecture does expose security-level ISIN in its listed-company / instrument-reference infrastructure. B3's official `BVBG.028.02 InstrumentReport` documentation defines an instrument file with an ISIN field, and official B3 listed-company pages visibly associate exact B3 trading codes with ISINs. This establishes that an authoritative ISIN class exists, but no already-materialized batch snapshot for the locked 98 rows exists in the repository and no compliant batch retrieval was completed in this gate.

The stop rule therefore prevents escalation into 79 search-engine or issuer-by-issuer recovery loops. No alternative provider loop was opened.

## 6. B3 identity semantics

For all 98 locked rows, the existing official B3 evidence already establishes:

- Primary MIC: `BVMF`
- exact B3 trading code / ticker
- official security name
- official B3 instrument-type label
- official IBrX 100 membership as of the source snapshot
- a stable security-level B3 code/ticker identity lineage.

The v0.31 identity gate previously passed all 98 rows under the then-authorized `Primary MIC + official ticker + stable WS_ID` fallback because the membership response carried no ISIN.

This validation gate does **not** promote that fallback to final canonical identity. The current Brazil policy requires exact security-level ISIN before later admission.

## 7. Instrument pre-filter

The frozen 98-row source contains:

- Ordinary/Common: **79**
- Preferred Shares: **12**
- Units: **7**
- Unknown instrument: **0**

Therefore:

- Eligible-for-Identity-Validation Rows: **79**
- Instrument-Policy-Excluded Rows: **19**
- Unknown Instrument Rows: **0**

The 19 excluded rows are evidence-classified only as `INSTRUMENT_POLICY_EXCLUDED`; this is not a new Admission outcome.

## 8. Primary listing validation

All 98 rows are official B3 IBrX 100 security-level rows with Primary MIC `BVMF` in the frozen lineage.

- Primary BVMF Listing Validated: **98**
- Primary-Listing Conflicts: **0**
- Primary Listing Validation: **PASS**

No foreign-secondary, ADR or BDR substitution was introduced.

## 9. Share-class validation

The official B3 type semantics in the frozen source classify all 98 rows without an UNKNOWN bucket:

- 79 ordinary/common (`ON...` family)
- 12 preferred (`PN...` family)
- 7 units (`UNT`/`UNIT` family)

No cross-class merge was performed.

- Exact Share Class Validated: **98**
- Share-Class Conflicts: **0**
- Share-Class Validation: **PASS**

## 10. ISIN validation

For the 79 policy-eligible Ordinary/Common rows, the locked official population source contains **no ISIN values**. The source explicitly records that it does not provide ISIN.

No ISIN was synthesized from ticker, CNPJ, issuer name or other identifiers. No ADR/BDR ISIN was substituted. No class ISIN was copied across securities.

The bounded official B3 method check established an authoritative ISIN evidence class, but not a compliant row-complete batch materialization for the 79 eligible rows within this stage. Continuing would require either a new controlled batch-evidence stage or prohibited security-by-security recovery.

Therefore:

- Identity/ISIN Validated Rows: **0**
- Identity Validated / ISIN Missing: **79**
- ISIN Identity Conflicts: **0**
- ISIN Syntax PASS: **0**
- ISIN Luhn PASS: **0**
- ISIN Validation: **FAIL**

The zero syntax/Luhn counts mean no candidate ISIN entered those checks; they do not represent syntactically invalid ISINs.

## 11. Security identity hard gate

The non-ISIN components of security identity are strong and systematic: BVMF, ticker, official security name and class are available for the full locked population.

However the target tuple is:

`ISIN + Primary_MIC + Primary_Ticker / Trading Code + Exact Security Name + Exact Share Class`

Because the required ISIN component is systematically absent for all 79 admission-relevant rows, final canonical security identity is incomplete.

- Security Identity Validation: **FAIL**
- Security Identity Problem: **YES**

This is a bounded missing-component problem, not an ambiguity in the B3 ticker or class architecture.

## 12. Corporate-action / currentness assessment

The locked population source is dated 2026-08-31. The existing B3 identity lineage is tied to that source date and does not show a row-level corporate-action conflict inside the 98-row snapshot.

No automatic successor mapping was attempted.

- Corporate-Action Problem: **NO structural problem observed in the locked evidence**
- Any future identity evidence must remain date-compatible with the 2026-08-31 population snapshot.

## 13. Research-Partial collision diagnostic

Brazil was already introduced historically as a 98-row workbench/current-master segment in the controlled v0.34 lineage, and the current 2527 Research Partial still reports 98 Brazil workbench rows.

The read-only diagnostic therefore records the locked Brazil population as already represented at the workbench BVMF+ticker level, without treating that as final canonical identity or admission under this new policy.

- Already-Present Diagnostics: **98**
- Potential Research-Partial Conflicts: **0 identified from the existing BVMF+ticker/security-lineage diagnostic**

Because ISIN is blank in the Brazil lineage, these diagnostics cannot substitute for future exact-ISIN collision adjudication.

## 14. Validation counts and rate

| Metric | Count |
|---|---:|
| Population Rows | 98 |
| Ordinary/Common Rows | 79 |
| Instrument-Policy-Excluded Rows | 19 |
| Unknown Instrument Rows | 0 |
| Eligible-for-Identity-Validation Rows | 79 |
| Identity/ISIN Validated Rows | 0 |
| Identity Validated / ISIN Missing | 79 |
| Share-Class Conflicts | 0 |
| Primary-Listing Conflicts | 0 |
| ISIN Identity Conflicts | 0 |
| Unresolved Rows outside the explicit ISIN-missing bucket | 0 |
| Already-Present Diagnostics | 98 |
| Potential Research-Partial Conflicts | 0 |

Validation Rate = `0 / 79 = 0.00%`.

The denominator excludes the 19 policy-excluded Preferred/Unit rows as required.

## 15. Manual recovery and failure-mode assessment

- Population Evidence Problem: **NO**
- Listing Architecture Problem: **NO**
- Security Identity Problem: **YES** — final canonical tuple incomplete because ISIN is absent
- ISIN Problem: **YES** — systematic across all 79 policy-eligible rows
- Share-Class Problem: **NO**
- Corporate-Action Problem: **NO structural problem observed**
- Generic Source Hunt Required: **NO for diagnosis; YES would be required if one tried to continue without a separately authorized batch path, therefore continuation is stopped**
- Expected Security-by-Security Manual Recovery: **HIGH** if attempted under the currently materialized evidence set
- Canada/Korea/US3 Failure-Mode Risk: **HIGH** if recovery were allowed to fan out row-by-row

The correct fail-closed action is to stop before such a recovery loop.

## 16. Identity/ISIN evidence sidecar

No new row-level Identity/ISIN sidecar is committed in this gate.

Reason: a compliant sidecar with the required validated-ISIN fields would contain no validated ISIN for any of the 79 eligible rows and would merely duplicate the locked 98-row source plus the already documented blank-ISIN condition. The authoritative row-level source remains `universe/segments/br_ibrx100_source_frozen_v0.32.csv`.

- Identity/ISIN Evidence Sidecar Created: **NO**
- Identity/ISIN Evidence Sidecar Path: **NONE**
- Evidence Sidecar SHA256: **NONE**

This does not alter the locked population or any existing evidence artifact.

## 17. Build readiness

**BUILD READINESS: BLOCKED**

Reason: Population evidence, BVMF listing and share-class architecture are strong, but the exact security-level ISIN hard gate fails systematically for all 79 policy-eligible rows. A Brazil Admission Build cannot be authorized while the policy requires exact ISIN and no compliant batch ISIN evidence has been materialized.

No per-security recovery loop is authorized.

## 18. Exact next authorized stage

**Brazil IBrX 100 Identity/ISIN Manager Gate — READ-ONLY**

That manager gate may decide whether one bounded batch-authoritative ISIN evidence path deserves a separate authorization or whether Brazil should be parked. It may not silently start recovery or an Admission Build.

## 19. No-touch confirmation

No population was rematerialized. No new population source was added. No Candidate Population was created. No Admission was performed. No Universe, Research Partial, Membership, Strict, Frozen, US-1, US-2, US-3, AU-1, Canada or Korea state was changed. No mapping, history, liquidity, eligibility, scan/U3K or productive v7.2 work was performed.

## 20. Quality gates G0-G17

- G0 Correct origin/main HEAD — PASS
- G1 Correct Brazil Identity/ISIN validation stage — PASS
- G2 Research Partial 2527 verified — PASS
- G3 Strict 759 verified — PASS
- G4 Frozen 0 verified — PASS
- G5 Exact existing 98-row population used — PASS
- G6 No population rematerialization — PASS
- G7 Instrument policy from prior gate retained — PASS
- G8 BVMF primary-listing validation performed — PASS
- G9 Security identity validation performed — PASS
- G10 Share-class validation performed — PASS
- G11 Exact security-level ISIN validation performed — PASS, result 0 validated / 79 missing under bounded evidence
- G12 Syntax + Luhn checks performed — PASS, no ISIN entered validation; 0 PASS values, no synthetic identifiers used
- G13 Research-Partial collision diagnostics performed — PASS
- G14 Manual-recovery / failure-mode risk assessed — PASS
- G15 Build Readiness exactly BLOCKED — PASS
- G16 No universe/membership write — PASS
- G17 No follow-on stage executed — PASS

**G0-G17: PASS**

## 21. Final state

**BRAZIL IBRX 100 IDENTITY / ISIN VALIDATION GATE — PASS**

**SECURITY IDENTITY VALIDATION: FAIL**

**ISIN VALIDATION: FAIL**

**SHARE-CLASS VALIDATION: PASS**

**PRIMARY LISTING VALIDATION: PASS**

**BUILD READINESS: BLOCKED**

**NEXT AUTHORIZED STAGE: Brazil IBrX 100 Identity/ISIN Manager Gate — READ-ONLY**

HARD STOP.