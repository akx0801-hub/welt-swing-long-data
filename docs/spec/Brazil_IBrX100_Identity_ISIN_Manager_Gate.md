# Brazil IBrX 100 Identity / ISIN Manager Gate

## Stage decision

**BRAZIL IBRX 100 IDENTITY / ISIN MANAGER GATE — PASS**

**RECOMMENDATION A — AUTHORIZE ONE TARGETED SCALABLE IDENTITY/ISIN EVIDENCE PATH**

**BRAZIL STATE AFTER: ACTIVE-EVIDENCE-ONLY**

**NEXT AUTHORIZED STAGE: Brazil IBrX 100 B3 InstrumentReport ISIN Qualification Gate — READ-ONLY / EVIDENCE ONLY / NO UNIVERSE WRITE**

This is a manager-decision-only stage. It performs no source hunt, no ISIN lookup, no B3/CVM/API request, no download, no security-by-security recovery, no evidence sidecar, no candidate generation, no admission, no build, no Research-Partial/Membership/Universe write, no Frozen write and no mapping/history/liquidity/eligibility/scan work.

## 1. Start HEAD and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `992c1f1364038f80f160fef246c993bd7ec5cb49`
- origin/main at startcheck: `992c1f1364038f80f160fef246c993bd7ec5cb49`
- Verified predecessor commit: `Brazil IBrX 100 identity ISIN validation gate`
- Authorized stage: **Brazil IBrX 100 Identity/ISIN Manager Gate — READ-ONLY**
- No completed report at this path existed at startcheck.

Central repository artifacts used:

- `docs/spec/Brazil_IBrX100_Identity_ISIN_Validation_Gate.md`
- `docs/spec/Brazil_IBrX100_Admission_Policy_Gate.md`
- `docs/spec/Post_US3_Next_Population_Manager_Gate.md`
- `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
- `universe/segments/br_ibrx100_source_frozen_v0.32.csv`
- `universe/segments/br_ibrx100_strict_ordinary_frozen_v0.32.csv`
- `docs/validation/Current_Master_Materialized_Official_Membership_Identity_Reconciliation_v0.31.md`
- `docs/validation/Current_Master_BR_IBRX100_Source_Segment_Freeze_Liquidity_Precheck_v0.32.md`
- `docs/spec/Canada_Targeted_Manual_Identity_Recovery_Report.md`
- `docs/spec/Canada_Targeted_Recovery_Manager_Gate.md`
- `docs/spec/Post_Korea_Evidence_Validation_Manager_Gate.md`
- `docs/spec/US3_Population_Evidence_Manager_Gate.md`
- `docs/spec/US3_Named_Index_Tracker_Qualification_Gate.md`
- `docs/spec/US1_Integration_Evidence_Gate_Report.md`
- `docs/spec/US2_SP400_Admission_Build_Report.md`
- `docs/spec/AU1_Post_Integration_Integrity_Audit.md`

No new source was searched or tested.

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
| Brazil | ACTIVE-MANAGER-ONLY |
| Brazil target | IBrX 100 |
| Primary market | B3 |
| Primary MIC | BVMF |
| Population rows | 98 |
| Ordinary/Common | 79 |
| Preferred | 12 |
| Units | 7 |
| Identity/ISIN validated | 0/79 |
| Population Evidence | PASS |
| Primary Listing Validation | PASS |
| Share-Class Validation | PASS |
| Security Identity Validation | FAIL |
| ISIN Validation | FAIL |
| Build Readiness | BLOCKED |

## 3. Exact failure diagnosis

Brazil is not blocked by population membership, B3 security codes, primary exchange, share-class semantics, population reproducibility, corporate actions or known Research-Partial collisions.

The single structural blocker is:

**SYSTEMATIC SECURITY-LEVEL ISIN EVIDENCE GAP — 79/79 policy-eligible Ordinary/Common securities have no authoritative exact security-level and share-class-level ISIN in the currently materialized Brazil evidence.**

The locked B3 population source explicitly records `Official_Source_Provides_ISIN = False`. Therefore the existing BVMF+ticker+name+class identity is insufficient under the Brazil Admission Policy hard gate.

## 4. Existing positive Brazil evidence

Brazil already has unusually strong preconditions compared with Canada/Korea:

- official B3 IBrX 100 population materialized and frozen;
- 98 security-level rows;
- 98 unique B3 security/trading codes;
- Primary MIC `BVMF` established;
- BVMF primary-listing context validated for all 98 rows;
- exact B3 type/share-class semantics validated for all 98 rows;
- 79 Ordinary/Common rows isolated deterministically;
- 12 Preferred and 7 Units already segregated by policy;
- Research-Partial diagnostic shows all 98 represented at BVMF+ticker workbench level with no identified current diagnostic conflict.

Thus the unresolved task is narrow: authoritative B3 security identity -> exact ISIN.

## 5. Existing evidence architecture assessment

The preceding validation report already documents one concrete official B3 evidence class:

**B3 `BVBG.028.02 InstrumentReport` instrument-reference / security-master evidence.**

The existing report states that official B3 `InstrumentReport` documentation defines an instrument file with an ISIN field. The same report also records that official B3 listed-company/instrument infrastructure associates exact B3 trading codes with ISINs.

This is sufficient for manager-level hypothesis specificity because the proposed path is not “search B3/CVM/issuers for ISINs.” It is one identified B3-authoritative instrument-master evidence class with an expected security-level ISIN field and a natural join to the already locked B3 trading-code/security identity.

What is not yet proven is the qualification-stage execution property: whether the relevant current file can actually be materialized reproducibly, whether its row schema maps the locked IBrX rows cleanly, and whether coverage is high enough. Those are exactly the questions for one bounded qualification gate.

## 6. Selected single evidence path

**Selected Evidence Path: official B3 BVBG.028.02 InstrumentReport security-master / instrument-reference dataset, joined to the locked IBrX-100 rows by authoritative B3 security/trading identity.**

Conceptual expected fields/capabilities already supported by repository evidence:

- authority/provider class: B3 official market infrastructure;
- security-level instrument records;
- ISIN field;
- B3 instrument/security identifiers sufficient to test mapping to the locked B3 trading code/security identity;
- instrument-level identity suitable for exact share-class consistency checks;
- dataset/batch principle rather than issuer-by-issuer recovery.

No endpoint, download method or current file instance is assumed or tested in this manager gate.

## 7. Evaluation matrix

| Dimension | Assessment | Manager reasoning |
|---|---|---|
| Evidence Authority | STRONG | B3 is the official primary-market infrastructure and existing Brazil source authority. |
| Evidence Hypothesis Specificity | HIGH | Exact named B3 instrument-report evidence class, exact blocker, exact qualification objective. |
| Security-Level Capability | STRONG | Existing report identifies B3 instrument-reference/security-level architecture. |
| Share-Class Capability | CONDITIONAL | Locked B3 class evidence is already strong; the qualification gate must prove row-level fidelity when joining InstrumentReport. |
| ISIN Capability | STRONG | Existing repository report explicitly documents an ISIN field in BVBG.028.02 InstrumentReport. |
| B3 Security-Code Mapping | STRONG | Locked population already carries exact B3 trading/security codes; path is same-authority B3 instrument identity. |
| Batch Coverage Potential | HIGH | InstrumentReport is a dataset/file architecture, not per-security lookup. |
| Expected Coverage | HIGH | A B3 instrument master should, if qualification succeeds, cover the 79 active B3 ordinary lines in one batch; this remains to be empirically measured. |
| Materialization Reproducibility | CONDITIONAL | Existence/capability documented; actual current materialization not yet proven. |
| Row-Level Reproducibility | CONDITIONAL | Must be demonstrated by deterministic join and coverage counts in the qualification gate. |
| Manual Recovery Requirement | LOW | No per-security recovery is needed if the dataset path qualifies. |
| Scalability | YES | One batch source can potentially resolve the complete 79-row gap. |
| Expected Information Value | HIGH | PASS unlocks the only central blocker; FAIL strongly supports parking Brazil. |
| Canada Failure-Mode Risk | LOW | No issuer-by-issuer recovery; one dataset qualification only. |
| Korea Failure-Mode Risk | LOW | Population/listing/class are already proven; only one narrow identity component remains. |
| US-3 Failure-Mode Risk | MEDIUM | Materialization can still fail despite a strong evidence hypothesis; one-shot stop rule controls this risk. |
| Overall Failure-Loop Risk | MEDIUM | Bounded to one qualification attempt with no fallback cascade. |

## 8. Canada failure-mode lesson

Canada produced 0/217 evidence-ready and then 0/30 targeted-recovery-ready with 0 verified ISIN and HIGH manual cost. The failure pattern was repeated security-by-security identity recovery without a scalable authoritative batch identity source.

The selected Brazil path is acceptable only because it is the opposite architecture: a single official B3 instrument-master dataset hypothesis. If the qualification gate cannot materialize and map it in batch, Brazil must not fall back to issuer sites, manual lookups or a second provider.

## 9. Korea failure-mode lesson

Korea produced 0/12 validation-ready, failed current KRX population/listing/security identity reproduction and had Source Scalability = NO.

Brazil differs materially because population evidence, BVMF listing and share class are already proven for 98/98. The proposed B3 InstrumentReport path addresses one isolated missing field family rather than rebuilding the entire identity chain.

Nevertheless, if the official B3 dataset cannot be reproducibly materialized and joined, the correct result is failure and park, not source variation.

## 10. US-3 failure-mode lesson

US-3 showed that a strong evidence hypothesis and qualification can still fail at actual materialization. Therefore this manager gate does not treat the documented InstrumentReport capability as proof of success.

The next stage must empirically verify:

- current official source authority;
- actual security-level rows;
- exact ISIN availability;
- mapping to B3 codes/tickers;
- share-class fidelity;
- batch coverage;
- materialization reproducibility;
- row-level reproducibility;
- measurable completeness.

If any central property fails, no second Brazil evidence route is authorized.

## 11. Positive-method transfer from US-1 / US-2 / AU-1

Only architectural principles are transferred:

- exact security identifiers rather than issuer similarity;
- batch/reproducible evidence;
- security-level and share-class fidelity;
- measurable coverage;
- deterministic collision/mapping checks;
- fail-closed unresolved rows;
- no guessed identifiers;
- sealed evidence before integration.

US-1/US-2/AU-1 sources themselves are not transferred to Brazil.

## 12. Batch and scalability assessment

The 79/79 gap is systematic, so a solution is economically acceptable only if it is dataset-level.

The B3 InstrumentReport hypothesis meets that manager criterion:

- one authority;
- one dataset class;
- one deterministic qualification procedure;
- one join concept to existing B3 security identity;
- one measurable coverage result.

**Manual per-security recovery: NO.**

**Scalability: YES, subject to qualification.**

No 79-row manual lookup process is authorized.

## 13. Expected information value

**Expected Information Value: HIGH.**

A PASS would establish that the central 79/79 blocker can be solved with one authoritative, scalable B3 source and would justify a later sidecar-only Brazil Admission Build under the unchanged ISIN hard gate.

A FAIL would demonstrate that the only currently documented concrete official batch ISIN path cannot be operationalized under the required reproducibility rules. Under the one-shot rule that would be strong evidence to park Brazil rather than enter recovery loops.

The test is therefore decision-useful in both directions.

## 14. Opportunity cost

**Opportunity Cost: LOW.**

The next step is one bounded qualification gate only. It does not authorize 79 manual cases or a source cascade. If the path fails, Brazil stops and manager attention can move to already documented alternatives such as Japan, Europe, Taiwan or India.

## 15. New evidence path exists

**New Evidence Path Exists: YES.**

The path is concrete enough under existing repository evidence to satisfy Option A minimum criteria. It is not a generic request to search for ISIN data.

## 16. Recommendation and decision

**Recommendation: A**

**Decision: AUTHORIZE ONE TARGETED SCALABLE IDENTITY/ISIN EVIDENCE PATH**

**Brazil State After: ACTIVE-EVIDENCE-ONLY**

Selected evidence path:

**B3 BVBG.028.02 InstrumentReport security-master / instrument-reference ISIN path.**

### Evidence Objective

Determine whether one current official B3 InstrumentReport dataset can be reproducibly materialized and deterministically joined to the locked 79 Ordinary/Common IBrX-100 rows so that exact security-level ISIN, B3 security identity and share class can be validated at high coverage without per-security recovery.

### Allowed Scope

- exactly the already documented B3 `BVBG.028.02 InstrumentReport` evidence class;
- official B3 only;
- qualification of source authority, currentness, security-level schema, ISIN field, B3 code/ticker join, share-class fidelity, batch coverage, materialization reproducibility and row-level reproducibility;
- locked 98-row IBrX population may be used only as join/coverage target;
- no admission/build/integration.

### Disallowed Scope

- CVM fallback;
- issuer-site fallback;
- another B3 dataset family after failure;
- another provider/registry;
- search-engine recovery;
- per-security ISIN lookup;
- population refresh;
- candidate generation;
- admission/build/universe write.

### Success Criteria

PASS only if the one B3 InstrumentReport path is demonstrated to be:

1. official and current enough for the 2026-08-31 locked population;
2. reproducibly materializable;
3. security-level;
4. ISIN-bearing;
5. deterministically mappable to authoritative B3 security/trading codes;
6. share-class faithful;
7. batch-capable across the 79 Ordinary/Common target rows;
8. measurably high-coverage with only a small isolated unresolved remainder at most;
9. row-level reproducible;
10. suitable for later exact syntax/Luhn/security-class validation without manual recovery.

### Failure Criteria

FAIL if the one path cannot be materialized reproducibly, lacks exact ISIN/security-level mapping, cannot preserve share-class identity, has materially incomplete unexplained coverage, requires per-security recovery, requires another source/provider, or otherwise cannot solve the systematic gap in a scalable batch form.

On FAIL: Brazil must be PARKED. No second evidence path is automatically authorized.

## 17. One-shot rule

The next qualification stage is a single attempt.

If it FAILS:

- Brazil -> PARKED;
- no second B3 source family;
- no CVM fallback;
- no issuer recovery;
- no provider cascade;
- no manual 79-security loop;
- no Admission Build.

Any future Brazil reactivation would require a separate later global manager decision.

## 18. Exact next authorized stage

**Brazil IBrX 100 B3 InstrumentReport ISIN Qualification Gate — READ-ONLY / EVIDENCE ONLY / NO UNIVERSE WRITE**

This stage may test only the selected B3 InstrumentReport path and must end PASS/FAIL. It may not run Admission.

## 19. No-touch confirmation

No source was searched. No ISIN was searched. No B3/CVM/API endpoint was tested. No download was attempted. No security was manually recovered. The 98-row Brazil population and all Research Partial, Membership, Universe, Strict, Frozen, US-1, US-2, US-3, AU-1, Canada and Korea states remain unchanged. No mapping/history/liquidity/eligibility/scan/U3K or productive v7.2 work was performed.

## 20. Quality gates G0-G17

- G0 Correct origin/main HEAD — PASS
- G1 Correct Brazil Identity/ISIN Manager stage — PASS
- G2 Research Partial 2527 verified — PASS
- G3 Strict 759 verified — PASS
- G4 Frozen 0 verified — PASS
- G5 Canada/Korea/US-3 remain PARKED — PASS
- G6 Brazil 98-row population remains unchanged — PASS
- G7 79 eligible Ordinary/Common rows recognized — PASS
- G8 0/79 validated ISIN failure recognized — PASS
- G9 No source hunt performed — PASS
- G10 No security-by-security recovery performed — PASS
- G11 Canada/Korea/US-3 failure modes incorporated — PASS
- G12 Exactly one potential evidence path assessed — PASS
- G13 Scalability and Expected Information Value assessed — PASS
- G14 Exactly one Recommendation A/B — PASS
- G15 Exact next authorized stage defined — PASS
- G16 No data/universe/membership change — PASS
- G17 No follow-on stage executed — PASS

**G0-G17: PASS**

## 21. Final state

**STAGE STATUS: PASS**

**RECOMMENDATION A**

**DECISION: AUTHORIZE ONE TARGETED SCALABLE IDENTITY/ISIN EVIDENCE PATH**

**SELECTED EVIDENCE PATH: B3 BVBG.028.02 InstrumentReport security-master / instrument-reference ISIN path**

**BRAZIL STATE AFTER: ACTIVE-EVIDENCE-ONLY**

**NEXT AUTHORIZED STAGE: Brazil IBrX 100 B3 InstrumentReport ISIN Qualification Gate — READ-ONLY / EVIDENCE ONLY / NO UNIVERSE WRITE**

HARD STOP.
