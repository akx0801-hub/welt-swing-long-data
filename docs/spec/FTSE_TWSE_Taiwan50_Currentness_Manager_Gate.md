# FTSE TWSE Taiwan 50 Currentness Manager Gate

## Stage decision

**STAGE STATUS: PASS**

**RECOMMENDATION: B**

**DECISION: PARK TAIWAN**

**TAIWAN STATE AFTER: PARKED**

**BUILD READINESS: BLOCKED**

**NEXT AUTHORIZED STAGE: Post-Taiwan Next-Population Manager Gate — READ-ONLY**

This is a manager-decision-only stage. No source hunt, endpoint test, raw materialization, current-population reconciliation, ISIN recovery, individual-security research, sidecar generation, candidate generation, admission build, Research-Partial/Membership/Universe/Strict/Frozen write, or productive Welt-Swing v7.2 work is performed.

## 1. Start HEAD and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `6ec62c8d895a018a335330f47809bf7bb8f5574f`
- origin/main at startcheck: `6ec62c8d895a018a335330f47809bf7bb8f5574f`
- Verified predecessor commit: `FTSE TWSE Taiwan 50 population identity currentness validation gate`
- Authorized stage: **FTSE TWSE Taiwan 50 Currentness Manager Gate — READ-ONLY**

Repository artifacts used include:

- `docs/spec/FTSE_TWSE_Taiwan50_Population_Identity_Currentness_Validation_Gate.md`
- `docs/spec/FTSE_TWSE_Taiwan50_Admission_Policy_Gate.md`
- `docs/spec/Post_Brazil_Next_Population_Manager_Gate.md`
- `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
- `output_current_master_reconciliation_v0_28/current_master_identity_quality_v0.28.csv`
- `output_current_master_reconciliation_v0_28/current_master_source_authority_audit_v0.28.csv`
- `output_current_master_missing_source_materialization_v0_29/imported_segment_provenance_carryforward_v0.29.csv`
- existing Taiwan workbench / Research-Partial rows carrying `SRC_FTSE_TW50_CW_20260630`
- prior Canada, Korea, US-3 and Brazil manager/validation artifacts already embedded in the current governance chain.

No external or experimental source was searched or tested.

## 2. Baseline

| Measure | State |
|---|---:|
| Research Partial | 2527 |
| Strict | 759 |
| Frozen | 0 |
| US-1 | 372 |
| US-2 | 369 |
| US Total | 741 |
| AU-1 | 153 |
| Usable Integrated Expansion Rows | 894 |
| Canada | PARKED |
| Korea | PARKED |
| US-3 | PARKED |
| Brazil | PARKED |
| Taiwan state before | ACTIVE-MANAGER-ONLY |

No baseline count is modified by this gate.

## 3. Taiwan locked facts

The repository confirms the following locked Taiwan facts:

- Population: **FTSE TWSE Taiwan 50**
- Primary Market: **Taiwan Stock Exchange**
- Primary MIC: **XTAI**
- Locked Source Lineage: `SRC_FTSE_TW50_CW_20260630`
- Locked Population As-of-Date: **2026-06-30**
- Locked Population Rows: **50**
- Existing Complete Security-Level ISIN Identity: **47/50**
- ISIN Gap Rows: **3/50**
- Historical Strict Coverage: **49/50**
- ISIN Gap Type: **ISOLATED**
- Population Boundary Clarity: **HIGH**
- Primary Listing Architecture: **STRONG**
- Local Security-Code Architecture: **STRONG**
- Canonical Identity Architecture: **STRONG**
- Security Identity Architecture: **STRONG**
- ISIN Architecture: **STRONG**
- Share-Class Architecture: **STRONG**

The governing problem is not the basic identity model. It is the inability to obtain reproducible row-level currentness evidence for the locked population.

## 4. Failed currentness validation summary

The immediately preceding currentness validation established:

- Currentness Evidence Authority: **STRONG**
- Raw Snapshot Materialized: **NO**
- Raw SHA256: **NONE**
- Materialization Reproducibility: **FAIL**
- Current Population Rows Observed: **NONE**
- Ambiguous Membership Rows: **50**
- Population Reconciliation Coverage: **0.00%**
- Existing Complete Identity Rows Checked: **47**
- Unresolved Identity Currentness: **47**
- Existing 47-Identity Validation Coverage: **0.00%**
- Primary Listing Currentness Coverage: **0.00%**
- Share-Class Currentness Coverage: **0.00%**
- Manual Recovery Required if continuing without a separately authorized architecture: **HIGH**
- Currentness Failure-Loop Risk: **HIGH**
- CURRENTNESS VALIDATION: **FAIL**
- BUILD READINESS: **BLOCKED**

This is the decision input for the present manager gate.

## 5. Canada failure mode

Canada remains PARKED. Its lesson is that security-level identity/evidence gaps cannot be solved economically by repeated per-security recovery attempts. Multiple gates and targeted recovery produced insufficient ready output at high manual cost.

**Manager implication for Taiwan:** any new Taiwan path that depends on manual security-by-security currentness recovery is disqualified.

## 6. Korea failure mode

Korea remains PARKED. Its lesson is that an institutional index and plausible market architecture do not suffice when population/listing/identity evidence cannot be reproducibly materialized at row level.

**Manager implication for Taiwan:** a descriptive FTSE/TWSE index framework without a reproducible row-complete current snapshot is insufficient.

## 7. US-3 failure mode

US-3 remains PARKED. A named-index tracker qualification could look methodically sound and still fail when actual raw materialization and row-level reproducibility were attempted.

**Manager implication for Taiwan:** theoretical availability or plausibility of a dataset is not enough. The next path would need already-documented evidence that practical materialization is likely to work.

## 8. Brazil failure mode

Brazil remains PARKED. Its official B3 InstrumentReport path was conceptually suitable, but the one-shot gate failed because raw bytes could not be reproducibly materialized and sealed.

**Manager implication for Taiwan:** another nominally official source is not a valid next step unless repository evidence already demonstrates a structurally different and reproducibly materializable route.

## 9. Taiwan failure mode

Taiwan differs positively from Canada, Korea and Brazil in that the locked population and historical identity architecture are already strong: 50 rows, XTAI, 47 complete ISIN identities and only three isolated ISIN gaps.

However, the current blocker is now the same operational class seen in US-3 and Brazil: **CURRENTNESS EVIDENCE MATERIALIZATION / REPRODUCIBILITY FAILURE**.

The previous validation could not materialize a row-complete current constituent/security snapshot. Therefore all 50 locked membership states remained ambiguous and all 47 complete identities remained unresolved for currentness.

A further stage is justified only if a different, concrete, already-repository-documented path can avoid this exact failure mode.

## 10. Existing documented evidence paths

Repository review found the following Taiwan evidence architecture already documented:

### 10.1 `SRC_FTSE_TW50_CW_20260630`

- Provider / authority class: FTSE TWSE Taiwan 50 institutional lineage already carried in the repository.
- Dataset / lineage: `SRC_FTSE_TW50_CW_20260630`.
- Security-level capability historically: strong enough to support 50 population rows and 47 strict ISIN+MIC+ticker identities.
- Population as-of: 2026-06-30.
- Currentness status: explicitly pending source/currentness audit in repository governance.
- Relationship to failed gate: this is the same lineage/currentness architecture whose row-complete current snapshot could not be reproducibly materialized.

This is **not structurally different** from the failed currentness path and therefore cannot qualify as the one new path.

### 10.2 Existing workbench / Research-Partial rows

Existing Taiwan workbench rows contain XTAI local codes, security names and many ISINs. They are historical internal state, not an independent current external evidence source. Using them as proof of their own currentness would be circular and is prohibited by the admission policy.

They therefore are **not a viable currentness evidence path**.

### 10.3 Existing source-authority / provenance audit artifacts

The repository audit artifacts document that Taiwan has 50 source rows and 47 complete identities, but they also explicitly classify source provenance/currentness as requiring audit/freeze validation. These artifacts describe the gap; they do not provide a distinct current security-level snapshot or endpoint.

They therefore are **not a viable currentness evidence path**.

### 10.4 Other possible classes

No repository artifact reviewed names a second concrete Taiwan dataset, file, feed, endpoint or security-master product that simultaneously provides current FTSE TWSE Taiwan 50 membership, exact XTAI local codes, share-class fidelity and batch-reproducible row-level currentness while being structurally different from the failed FTSE/TWSE currentness route.

Ideas such as another FTSE download, a TWSE page, an ETF, a generic provider, issuer sites or manual per-security checks are not already-qualified repository paths and would constitute a prohibited source hunt.

## 11. New-currentness-path test

The hard manager test requires all of the following to be known from repository evidence: provider/institution, exact dataset/product/file/endpoint, security-level currentness capability, exact locked-50 reconciliation capability, reproducible materialization expectation, structural difference from the failed route, and no per-security recovery.

The reviewed repository evidence does not satisfy this test for any second path.

**New Currentness Evidence Path Exists: NO.**

**Number of Viable Evidence Paths: 0.**

## 12. Selected evidence path assessment

**Selected Evidence Path: NONE.**

Because no viable path exists, the path-specific assessment is not applicable:

- Selected Provider / Authority: **NONE**
- Already Documented in Repo: **N/A**
- Structurally Different From Failed Currentness Path: **N/A**
- Evidence Authority: **N/A**
- Security-Level Capability: **N/A**
- Current Membership Capability: **N/A**
- XTAI Listing Capability: **N/A**
- Local-Code Mapping Capability: **N/A**
- Share-Class Capability: **N/A**
- ISIN Capability: **N/A**
- Existing 47 Identity Revalidation Capability: **N/A**
- Corporate-Action Detection Capability: **N/A**
- Batch Capability: **N/A**
- Expected Batch Coverage: **N/A**
- Expected Materialization Reproducibility: **N/A**
- Expected Row-Level Reproducibility: **N/A**
- Expected Manual Recovery: **N/A**
- Scalability: **N/A**

## 13. Authority assessment

The authority of the previously used FTSE/TWSE evidence class remains strong. That does not satisfy Option A because authority is only one hard criterion. The failed gate demonstrated that current row-level materialization and reproducibility, not institutional authority, is the binding failure.

No alternative path with separately established authority and concrete dataset identity is documented.

## 14. Security-level capability

Historical Taiwan rows demonstrate a strong security-level architecture. But no second documented currentness source exists that can be manager-assessed as security-level **STRONG** for current row-level evidence.

Option A therefore fails this requirement for any new path.

## 15. Current-membership capability

No distinct documented dataset can presently be identified from repository evidence as capable of deterministic `locked 50` versus `current constituent population` reconciliation.

Option A therefore fails this requirement.

## 16. Local-code capability

The locked lineage itself has strong XTAI local-code identity. But no separately documented currentness dataset is available to confirm those codes across the current population in a structurally different way.

Option A therefore fails at the path level even though the underlying identity architecture remains strong.

## 17. Share-class capability

Historical share-class architecture remains strong. A new currentness path, however, must itself provide or support reliable class continuity. No distinct documented path meets this condition.

## 18. Existing 47-identity revalidation capability

The previous gate left all 47 complete identities unresolved for currentness. No second documented source is available that can already be assessed as capable of revalidating current security, XTAI listing, local code, name and share class in batch.

**Existing 47 Identity Revalidation Capability for a new path: N/A because no viable path exists.**

## 19. Batch capability

No new path exists to qualify. Attempting manual checks across 50 securities would violate the batch requirement and reproduce the Canada failure mode.

**Batch Capability: N/A.**

## 20. Materialization reproducibility expectation

The failed path produced Materialization Reproducibility = FAIL. No structurally different repository-documented alternative has evidence supporting HIGH or strongly justified MEDIUM expected materialization reproducibility.

Therefore Option A cannot be authorized.

## 21. Row-level reproducibility expectation

The failed validation produced 0.00% row-level currentness coverage. No alternate documented path provides grounds for an expected HIGH row-level reproducibility rating.

Therefore Option A cannot be authorized.

## 22. Manual-recovery assessment

If Taiwan were continued without a new batch path, the remaining route would devolve into security-by-security checking or an undeclared source search.

**Expected Manual Recovery: HIGH in any unauthorized continuation scenario.**

**Individual Security Recovery Required to continue without a new path: YES.**

This is itself disqualifying for Option A.

## 23. Scalability

There is no viable selected path to rate as scalable. The only known continuation without new architecture would not be scalable.

**Scalability of a viable new path: N/A.**

## 24. Failure-loop risk

Risk assessments after incorporating the failed Taiwan currentness gate:

- Canada Failure-Mode Risk: **MEDIUM** — manual recovery would become the fallback if governance were relaxed.
- Korea Failure-Mode Risk: **HIGH** — authoritative index architecture exists but reproducible row-level currentness evidence is absent.
- US-3 Failure-Mode Risk: **HIGH** — materialization/reproducibility failure is directly analogous.
- Brazil Failure-Mode Risk: **HIGH** — official-source plausibility did not translate into reproducible raw evidence.
- Taiwan Repeat-Failure Risk: **HIGH** — repeating the same architecture or searching broadly would likely reproduce the failure.
- Overall Failure-Loop Risk: **HIGH**.

Option A is forbidden when overall failure-loop risk is HIGH.

## 25. Expected information value

No concrete second path exists. Authorizing an unspecified search or retry would have **LOW** expected information value because a PASS/FAIL outcome is not attached to a bounded, pre-identified evidence mechanism.

By contrast, parking Taiwan gives a clear governance result and prevents another uncontrolled recovery loop.

**Expected Information Value of a further unspecified Taiwan evidence gate: LOW.**

## 26. Opportunity cost

Other documented population candidates remain available for manager evaluation while Canada, Korea, US-3, Brazil and now Taiwan have accumulated evidence/materialization failure lessons.

Further Taiwan work without a concrete second path would consume effort with no bounded success mechanism.

**Opportunity Cost: HIGH.**

Sunk cost is not a reason to continue.

## 27. Recommendation

**Recommendation: B.**

Option A fails because there is no exactly identified, already-documented, structurally different, batch-capable currentness dataset/path with strong security-level/current-membership/local-code capability and high expected row-level reproducibility.

## 28. Decision

**Decision: PARK TAIWAN.**

**New Currentness Evidence Path Exists: NO.**

**Selected Evidence Path: NONE.**

No further Taiwan currentness evidence qualification is authorized by this gate.

## 29. Taiwan state after

**Taiwan State After: PARKED.**

This is a governance state only. No population, Research Partial, Membership, Strict, Frozen or Universe data is changed.

## 30. Build readiness

**BUILD READINESS: BLOCKED.**

The currentness blocker remains unresolved and no authorized evidence path remains.

## 31. Exact next authorized stage

**Post-Taiwan Next-Population Manager Gate — READ-ONLY**

Taiwan may not be automatically reactivated by that stage.

## 32. No-touch confirmation

No changes were made to Research Partial, Membership, Universe, Strict, Frozen, US-1, US-2, US-3, AU-1, Canada, Korea, Brazil, the locked Taiwan 50-row population, mapping, history, liquidity, eligibility, scan/U3K or productive Welt-Swing v7.2. No raw snapshot, evidence sidecar, candidate population or admission file was created. No follow-on stage was executed.

## 33. Quality gates G0-G17

- G0 Correct origin/main HEAD — **PASS**
- G1 Correct Taiwan Currentness Manager stage — **PASS**
- G2 Research Partial 2527 verified — **PASS**
- G3 Strict 759 verified — **PASS**
- G4 Frozen 0 verified — **PASS**
- G5 Canada/Korea/US-3/Brazil remain PARKED — **PASS**
- G6 Taiwan locked population remains 50 — **PASS**
- G7 Failed currentness validation correctly incorporated — **PASS**
- G8 No new source hunt performed — **PASS**
- G9 Only already-documented evidence paths assessed — **PASS**
- G10 Canada/Korea/US-3/Brazil failure modes incorporated — **PASS**
- G11 One-path-or-park rule applied — **PASS**
- G12 Materialization and row-level reproducibility explicitly assessed — **PASS**
- G13 Manual recovery / scalability assessed — **PASS**
- G14 Exactly one Recommendation A/B — **PASS**
- G15 Taiwan State After exactly PARKED — **PASS**
- G16 No universe/research/membership/strict/frozen write — **PASS**
- G17 No follow-on stage executed — **PASS**

**G0-G17: PASS**

## 34. Final state

**STAGE STATUS: PASS**

**RECOMMENDATION: B**

**DECISION: PARK TAIWAN**

**TAIWAN STATE AFTER: PARKED**

**BUILD READINESS: BLOCKED**

**NEXT AUTHORIZED STAGE: Post-Taiwan Next-Population Manager Gate — READ-ONLY**

HARD STOP.
