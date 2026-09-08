# Brazil IBrX 100 Admission Policy Gate

## Stage decision

**BRAZIL IBRX 100 ADMISSION POLICY GATE — PASS**

**BUILD READINESS: READY WITH CONDITIONS**

**NEXT AUTHORIZED STAGE: Brazil IBrX 100 Identity/ISIN Validation Gate — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

This is a policy-only gate. It performs no source hunt, no population rematerialization, no individual-security research, no candidate build, no admission, no Research-Partial/Membership/Universe write, no Frozen write, and no mapping/history/liquidity/eligibility/scan work.

## 1. Start HEAD and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `1634da03e26d7c10f4527c9d5de56184a92ac394`
- origin/main at startcheck: `1634da03e26d7c10f4527c9d5de56184a92ac394`
- Verified predecessor commit: `Post-US3 next population manager gate`
- Authorized stage: **Brazil IBrX 100 Admission Policy Gate — READ-ONLY**
- No completed report at `docs/spec/Brazil_IBrX100_Admission_Policy_Gate.md` existed at startcheck.

Central repository artifacts actually used include:

- `docs/spec/Post_US3_Next_Population_Manager_Gate.md`
- `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
- `docs/validation/Current_Master_Materialized_Official_Membership_Identity_Reconciliation_v0.31.md`
- `docs/validation/Current_Master_BR_IBRX100_Source_Segment_Freeze_Liquidity_Precheck_v0.32.md`
- `scripts/current_master_materialized_official_membership_identity_reconciliation_v0_31.py`
- `scripts/current_master_br_ibrx100_source_segment_freeze_liquidity_precheck_v0_32.py`
- `docs/spec/US2_Admission_Policy_ReadOnly.md`
- `docs/spec/US1_Integration_Evidence_Gate_Report.md`
- `docs/spec/Post_Integration_Integrity_Audit_US1_US2.md`
- `scripts/au1_admission_policy_readonly.py`

No new source was queried and no filename was invented.

## 2. Governance and baseline

WELT-SWING LONG DEV remains **DEV / RESEARCH / SHADOW**. Welt-Swing v7.2 remains the **SOLE PRODUCTIVE AUTHORITY**. Membership != Identity != Eligibility != Scan != Execution. Alpha Vantage remains prohibited.

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
| Usable integrated expansion rows | 894 |
| Canada | PARKED |
| Korea | PARKED |
| US-3 | PARKED |
| Selected next population | Brazil — IBrX 100 |
| Primary market | B3 |
| Primary MIC | BVMF |

The existing Brazil workbench rows are not automatically canonical admission rows.

## 3. Population boundary

The sole population boundary is:

**the already materialized current official B3 IBrX 100 security-level portfolio represented by the v0.30/v0.31 evidence lineage and frozen in v0.32.**

It is not all B3, all Brazil, Ibovespa, Brazilian ADRs, Brazilian issuers listed abroad, a free-form Brazil screen, or all existing Brazil Research-Partial rows.

A later build may consider only securities whose IBrX 100 membership is present in the authorized official B3 snapshot lineage.

## 4. Existing B3 population evidence

Repository evidence establishes:

- Source authority: **B3**
- Official source route: **GetPortfolioDay**
- Population: **IBrX 100**
- Official source rows: **98**
- Unique B3 security codes: **98**
- Official B3 header date: `31/08/26`
- Stored source As-of-Date: **2026-08-31**
- Source-AsOf semantics: `OFFICIAL_B3_HEADER_DATE_UNINTERPRETED`
- Primary MIC: **BVMF**
- v0.32 froze the 98-row source ledger byte-exactly from the v0.31 reconciliation ledger.

The same lineage also records 79 Strict Ordinary candidates and 19 instrument FAIL rows: 12 Preferred Shares and 7 Units. These counts are historical evidence only in this policy gate; no row is reclassified here.

## 5. Population Evidence Hard Gate

**Population Evidence Hard Gate: PASS**

Reason:

- official source authority is B3;
- the population is explicitly IBrX 100;
- the materialized source is security-level;
- all 98 rows have unique B3 security codes;
- the source was successfully batch-materialized and then frozen reproducibly in repository artifacts;
- the population count and source date are measurable;
- the source provides sufficient B3 security-code/ticker/type structure for later reconciliation.

No new population evidence gate is required before admission policy work. This PASS does not imply 98 admissions.

**Population Reproducibility: STRONG.**

## 6. Primary-market policy

For Brazil admission the relevant primary market is **B3** with Primary MIC **BVMF**.

Later admission requires evidence that the concrete security itself is the B3 primary security. A security is not Brazil-admissible merely because it trades on B3.

Required later listing identity:

- `Primary_MIC = BVMF`
- exact official B3 trading code / ticker
- exact security name
- exact share class / instrument form
- current listing state compatible with the population As-of-Date

Foreign secondary listings and depositary wrappers whose underlying primary security is outside B3 are not Brazil canonical primary securities.

## 7. B3 security-code and ticker semantics

Repository evidence already demonstrates that B3 supplies official security/trading codes and an official instrument-type description at security level.

Policy:

- B3 Trading Code is the candidate `Primary_Ticker` only after current BVMF primary-listing evidence is satisfied.
- B3 Security Code / Trading Code identifies a security-level traded line, not an issuer.
- Instrument Type and exact Share Class are separate identity dimensions and may not be inferred solely from issuer name.
- Multiple B3 instruments of the same issuer remain separate securities until canonical class selection rules are applied.
- Ticker suffix/end-digit semantics may be supporting evidence, never the sole identity proof when official security-level evidence is missing or contradictory.

The prior internal fallback `WS:BVMF:<official B3 ticker>` remains historical lineage evidence; this policy gate does not treat that fallback as sufficient for final admission because this gate imposes an explicit exact-ISIN hard gate.

**B3 Security Code Architecture: STRONG.**

## 8. Instrument policy matrix

| Instrument category | Policy outcome | Rationale |
|---|---|---|
| Ordinary / Common Equity | POTENTIALLY ADMIT | Standard U3K instrument class, subject to all remaining gates. |
| Preferred Share | EXCLUDE | Brazil-specific v0.31 evidence identified PN/PNA/PNB/PNC as separate B3 securities, but the authoritative DEV U3K instrument gate explicitly treats Preferred Shares as Standard-FAIL; v0.31 already classified 12 Brazil Preferred rows as instrument FAIL. This is not copied from US policy. |
| Unit | EXCLUDE | Units can be separately traded B3 securities, but the authoritative DEV U3K instrument gate explicitly excludes Units; v0.31 already classified 7 Brazil Unit rows as instrument FAIL. No decomposition into underlyings is permitted. |
| ETF / Fund | EXCLUDE | Non-ordinary fund instrument; outside U3K primary-equity definition. |
| BDR | EXCLUDE | Depositary receipt / wrapper; normally not the B3 primary equity of the underlying foreign issuer. |
| ADR / DR | EXCLUDE | Depositary wrapper rather than the B3 local primary share. |
| Rights / Warrants / Subscription Rights | EXCLUDE | Non-equity or temporary derivative-like instruments prohibited by DEV instrument gate. |
| Receipts / unresolved depositary structures | EXCLUDE | Cannot serve as canonical Brazil primary ordinary equity. |
| Structured Products | EXCLUDE | Outside primary common/ordinary equity scope. |
| Debt | EXCLUDE | Outside equity universe. |
| Foreign Secondary Listing | EXCLUDE | B3 trading alone does not make the instrument the canonical primary security. |
| Unknown / unresolved instrument type | REVIEW | Fail closed until exact instrument semantics are established; never direct admit. |

The policy distinguishes Brazil market structure from US market structure, but it must still remain compatible with the currently authoritative DEV U3K definition: the scan universe consists of sufficiently liquid primary-listed Ordinary/Common Shares and the instrument gate explicitly Standard-FAILs Preferred Shares and Units.

## 9. Ordinary/Common policy

**Ordinary/Common: POTENTIALLY ADMIT** only when every later hard gate passes:

1. current official IBrX 100 membership in the frozen B3 source lineage;
2. Primary Market B3 / `BVMF`;
3. exact current B3 trading code;
4. exact security name;
5. exact share class;
6. exact valid security-level ISIN;
7. no unresolved collision with the full Research Partial;
8. no unresolved corporate-action or successor ambiguity.

`ON` in B3 instrument semantics is supporting official evidence for Ordinary Share treatment; it does not waive any identity or ISIN requirement.

## 10. Preferred-share policy

**Preferred: EXCLUDE.**

Brazilian preferred shares are recognized as separate B3-traded securities with their own trading codes and class semantics; therefore they must never be silently merged with an ordinary class. However, the authoritative WELT-SWING LONG DEV instrument gate defines Preferred Shares as Standard-FAIL for the U3K, and the Brazil-specific v0.31 process already classified the 12 PN-family IBrX rows as instrument FAIL.

This exclusion is therefore based on the current global DEV universe definition plus Brazil-specific repository evidence, not on analogy to US preferred-stock treatment.

A future change to permit Brazil preferred classes would require a separate explicit DEV-rule change; this policy gate is not authorized to alter the master.

## 11. Unit policy

**Units: EXCLUDE.**

A B3 Unit may be a separately traded security with its own code and may combine underlying share classes. It must not be synthetically decomposed and must not inherit an underlying ISIN or identity.

The current DEV instrument gate explicitly Standard-FAILs Units, and v0.31 already classified seven IBrX rows as Unit instrument FAIL. Therefore Units are not eligible for direct Brazil canonical Primary-Scan admission under the current master.

## 12. BDR / foreign-listing policy

**BDR: EXCLUDE.**

A BDR is a depositary representation and does not become the Brazil canonical primary equity merely because it trades on B3. The underlying foreign primary security remains the identity-driving equity unless a future explicit architecture says otherwise.

**ADR/DR: EXCLUDE.**

**Foreign Secondary Listings: EXCLUDE.**

No ADR/BDR/secondary-listing substitution is allowed to satisfy local-share identity.

## 13. Canonical identity policy

Target identity for any later admitted Brazil security is exactly:

`ISIN + Primary_MIC + Primary_Ticker / Trading Code + Exact Security Name + Exact Share Class`

For Brazil:

- ISIN: exact security-level ISIN
- Primary MIC: `BVMF`
- Primary Ticker: exact current B3 trading code
- Security Name: exact current security name
- Share Class: exact traded class / instrument form

Issuer identity and security identity are separate. CNPJ, issuer name, economic group, ticker stem or similar names cannot replace security-level identity.

## 14. ISIN hard gate

**ISIN Required: YES.**

For later admission the ISIN must be:

- non-empty;
- syntactically valid;
- Luhn PASS;
- tied to the exact concrete security;
- tied to the exact share class;
- compatible with the current B3 security/trading-code identity.

Forbidden:

- guessing an ISIN;
- generating ISIN from ticker or CNPJ;
- using issuer-level identifiers in place of security ISIN;
- copying an ISIN across classes;
- using an ADR/BDR ISIN for the underlying local B3 share.

Important repository fact: the v0.30/v0.31 official B3 membership response did **not** contain authoritative ISINs and v0.31 left ISIN blank while using the master-permitted MIC+ticker+WS_ID fallback for that earlier stage. This new Brazil Admission Policy requires exact ISIN before admission, so the existing fallback is not sufficient for the next build.

## 15. ISIN evidence hierarchy

For later bounded validation:

1. **R1 — B3 / official exchange or market-infrastructure security-level evidence**
2. **R2 — official issuer / regulatory / registry evidence** with exact class-level linkage
3. **R3 — other already-qualified institutional security-level evidence** with exact security/class provenance
4. Secondary sources — discovery/cross-check only

Any disagreement with a higher-ranked source produces REVIEW/CONFLICT, not silent repair.

If exact ISIN cannot be established under a bounded reproducible evidence path, the security cannot be admitted.

## 16. Share-class policy

Multiple share classes of the same issuer are separate securities.

They must not be issuer-deduplicated. However, only instrument classes allowed by the current master can become Primary-Scan candidates.

Thus:

- multiple admissible Ordinary/Common classes may remain separately identified;
- the DEV `CANONICAL_SCAN_CLASS` rule may later select one ordinary/common primary scan class based on primary-market liquidity;
- excluded Preferred or Unit classes remain distinct identity records for evidence/collision purposes but cannot be promoted as U3K scan securities under current rules;
- no identity merge is allowed across classes.

**Share-Class Architecture: STRONG.**

## 17. Corporate-action policy

Fail closed for:

- ticker changes;
- mergers/acquisitions;
- spin-offs;
- ordinary/preferred conversions;
- unit formation or dissolution;
- stock splits / reverse splits;
- delistings;
- successor securities;
- recent index replacements;
- name or class changes.

Population As-of-Date, identity evidence date and corporate-action state must be temporally compatible.

No automatic successor mapping is permitted. If current security identity cannot be proven, outcome is REVIEW.

**Corporate-Action Architecture: CONDITIONAL** because the rules are defined but row-level currentness is not validated in this policy-only stage.

## 18. Research-Partial collision policy

A later build must check every authorized IBrX row against the full existing Research Partial, not only Brazil rows.

Required diagnostics:

1. exact canonical tuple;
2. exact ISIN;
3. Primary MIC + ticker;
4. exact/security-normalized name;
5. exact share class;
6. issuer/name similarity as a warning signal only;
7. corporate-action successor relation.

Build-sidecar outcomes:

- `ALREADY_PRESENT` — same concrete security already canonical;
- `NEW_CANDIDATE` — new security and every admission gate passes;
- `REVIEW` — identity/ISIN/class/corporate-action ambiguity;
- `CONFLICT` — contradictory canonical identifiers.

No actual row receives an outcome in this policy stage.

**Full Research Partial Collision Check Required: YES.**

## 19. Same-ISIN conflict policy

If the same ISIN appears with divergent Primary MIC, Primary Ticker, Security Name or Share Class, no new row is automatically created.

Outcome: **CONFLICT / REVIEW** until the exact current security identity is resolved.

Same issuer is not same security. Separate ordinary/common classes can remain separate if they possess distinct exact security identities and are otherwise allowed by the U3K instrument gate.

**Collision Architecture: STRONG.**

## 20. Identity architecture assessment

| Capability | Assessment | Reason |
|---|---|---|
| Population Reproducibility | STRONG | Official B3 membership successfully batch-materialized and frozen. |
| B3 Security Code Architecture | STRONG | 98/98 unique official codes, official ticker/type semantics. |
| Primary Listing Architecture | STRONG | B3/BVMF explicitly documented in repository lineage. |
| Security Identity Architecture | CONDITIONAL | MIC+ticker+WS_ID lineage is strong, but this policy requires exact ISIN before admission. |
| Share-Class Architecture | STRONG | Classes remain security-level distinct; no issuer-level merge. |
| ISIN Architecture | CONDITIONAL | Exact ISIN is mandatory, but official population source did not provide it. |
| Corporate-Action Architecture | CONDITIONAL | Fail-closed policy defined; row currentness still needs later validation. |
| Collision Architecture | STRONG | Full Research-Partial and same-ISIN conflict rules are defined. |

## 21. Canada / Korea / US-3 failure-mode assessment

Brazil differs materially from the parked paths:

- Population Source Already Materialized: **YES**
- Population Reproducibility: **STRONG**
- Security Codes Available: **YES**
- Identity Problem Bounded: **YES**
- ISIN Problem Bounded: **YES**
- Generic Source Hunt Required: **NO**
- Expected Security-by-Security Manual Recovery: **MEDIUM**
- Canada/Korea/US3 Failure-Mode Risk: **MEDIUM**

The risk is not population acquisition; it is exact class-level ISIN completion and current identity confirmation. This must be handled in one bounded validation gate. If that gate cannot produce reproducible class-level ISIN evidence, the process must fail closed rather than fan out into manual security-by-security recovery.

## 22. Build readiness

**BUILD READINESS: READY WITH CONDITIONS**

The policy is complete and the population-evidence hard gate passes. BVMF, instrument, share-class, corporate-action and collision rules are sufficiently defined.

The single remaining pre-build condition is material: the existing B3 population source has no authoritative ISIN field, whereas this Brazil policy now requires exact valid class-level ISIN for admission. Therefore an Admission Build is not yet authorized.

The condition is narrow and explicit: validate exact Security-level ISIN and corresponding current BVMF security identity through a bounded, reproducible evidence process without generic source hunt or guessed identifiers.

## 23. Exact next authorized stage

**NEXT AUTHORIZED STAGE: Brazil IBrX 100 Identity/ISIN Validation Gate — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

That gate may validate only the bounded identity/ISIN condition for the already materialized official IBrX population. It must not rematerialize population membership, perform admission, perform liquidity/history/eligibility work, or write the Universe.

## 24. No-touch confirmation

No B3 source was downloaded. The population was not rematerialized. No individual security was researched. No candidate/admission/evidence sidecar was created. No Research Partial, Membership, Strict, Frozen, Universe, US-1, US-2, AU-1, Canada, Korea or US-3 state was changed. No follow-on stage was executed.

## 25. Quality gates G0-G17

- G0 Correct origin/main HEAD — PASS
- G1 Correct Brazil IBrX 100 policy-only stage — PASS
- G2 Research Partial 2527 verified — PASS
- G3 Strict 759 verified — PASS
- G4 Frozen 0 verified — PASS
- G5 Canada/Korea/US-3 remain PARKED — PASS
- G6 Exact IBrX 100 population boundary defined — PASS
- G7 Existing 98-row B3 evidence assessed without rematerialization — PASS
- G8 BVMF primary-market policy defined — PASS
- G9 Instrument policy including Common/Preferred/Units/BDR defined — PASS
- G10 Canonical security-level identity policy defined — PASS
- G11 ISIN hard gate and evidence hierarchy defined — PASS
- G12 Share-class and corporate-action policy defined — PASS
- G13 Full Research-Partial collision policy defined — PASS
- G14 Failure-mode controls assessed — PASS
- G15 Build Readiness exactly READY WITH CONDITIONS — PASS
- G16 No data/universe change — PASS
- G17 No follow-on stage executed — PASS

**G0-G17: PASS**

## 26. Final state

**BRAZIL IBRX 100 ADMISSION POLICY GATE — PASS**

**Population Evidence Hard Gate: PASS**

**BUILD READINESS: READY WITH CONDITIONS**

**NEXT AUTHORIZED STAGE: Brazil IBrX 100 Identity/ISIN Validation Gate — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

HARD STOP.