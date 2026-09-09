# Post-Brazil Next-Population Manager Gate

## Stage decision

**POST-BRAZIL NEXT-POPULATION MANAGER GATE — PASS**

**RECOMMENDATION A — AUTHORIZE NEXT POPULATION POLICY GATE**

**SELECTED NEXT POPULATION: FTSE TWSE Taiwan 50**

**NEXT AUTHORIZED STAGE: FTSE TWSE Taiwan 50 Admission Policy Gate — READ-ONLY**

This is a read-only manager decision. It performs no source hunt, no population materialization, no candidate generation, no admission/build, no Research-Partial/Membership/Universe/Frozen write, no mapping/history/liquidity/eligibility/scan work and no productive Welt-Swing v7.2 change.

## 1. Start HEAD and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `20ec25e0e54a65ae3d49feb7fcb064df7c0aaaf8`
- origin/main at startcheck: `20ec25e0e54a65ae3d49feb7fcb064df7c0aaaf8`
- Verified predecessor commit: `Brazil IBrX 100 B3 InstrumentReport ISIN qualification gate`
- Authorized stage: **Post-Brazil Next-Population Manager Gate — READ-ONLY**

Central repository/governance artifacts actually used include:

- `docs/spec/Brazil_IBrX100_B3_InstrumentReport_ISIN_Qualification_Gate.md`
- `docs/spec/Brazil_IBrX100_Identity_ISIN_Manager_Gate.md`
- `docs/spec/Brazil_IBrX100_Identity_ISIN_Validation_Gate.md`
- `docs/spec/Brazil_IBrX100_Admission_Policy_Gate.md`
- `docs/spec/Post_US3_Next_Population_Manager_Gate.md`
- `docs/spec/Post_Korea_Next_Population_Manager_Gate.md`
- `docs/spec/P5_0_Architecture_Coverage_Gate.md`
- `output_current_master_reconciliation_v0_28/current_master_identity_quality_v0.28.csv`
- `output_current_master_reconciliation_v0_28/current_master_source_authority_audit_v0.28.csv`
- `output_current_master_missing_source_materialization_v0_29/imported_segment_provenance_carryforward_v0.29.csv`
- relevant existing US-1/US-2/AU-1/Canada/Korea/US-3 audit and manager artifacts.

No new source, provider, endpoint, constituent list, ETF, holdings or Security Master was searched or tested.

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
| Usable Integrated Expansion Rows | 894 |
| Canada | PARKED |
| Korea | PARKED |
| US-3 | PARKED |
| Brazil | PARKED |

Research Partial 2527 remains Workbench/Research state, not productive U3K Membership. Strict 759 is not a Membership tier. Frozen remains 0.

## 3. Parked populations and failure-mode lessons

### Canada
Canada remains PARKED. Multiple exact-identity/evidence attempts and targeted recovery produced zero ready output, with high manual cost and limited scalability. Manager lesson: ticker/listing context is insufficient when exact Security/Class/ISIN must be recovered security-by-security.

### Korea
Korea remains PARKED. The KOSPI 200 path was strategically attractive but current population/listing/Security Identity evidence was not reproducible enough and Source Scalability was NO. Manager lesson: an institutional index name alone is insufficient without practical row-level evidence.

### US-3
US-3 remains PARKED. Population boundary, US identity architecture and the named-index tracker hypothesis were strong, but v2 failed on raw materialization/sealing and row-level reproducibility. Manager lesson: qualification-level plausibility does not substitute for reproducible materialization.

### Brazil
Brazil remains PARKED. Population Evidence, BVMF Listing and Share Class were strong and a concrete official B3 InstrumentReport ISIN path existed, but the one-shot qualification failed because current raw bytes could not be reproducibly materialized/sealed and therefore no deterministic 79-row ISIN mapping could be established. Manager lesson: even a correct official dataset family is insufficient if operational materialization cannot be proven.

## 4. Existing workbench coverage

Existing Research-Partial/workbench populations remain:

| Segment | Rows | Existing repository role |
|---|---:|---|
| Europe — STOXX Europe 600 | 600 | conversion/workbench |
| Japan — Nikkei 225 | 225 | stage_strict/workbench |
| China — CSI 300 | 300 | stage_strict/workbench |
| Taiwan — FTSE TWSE Taiwan 50 | 50 | stage_strict/workbench |
| India — Nifty 50 | 50 | stage_strict/workbench |
| Hong Kong — Hang Seng Index | 93 | conversion/workbench |
| Brazil — IBrX 100 | 98 | parked |

These rows are not canonical Membership simply because they exist in Research Partial.

## 5. Candidate set

Only repository-grounded candidates were evaluated. Canada, Korea, US-3 and Brazil were not reactivated. No new AU-2 or post-US3 disjoint US population with stronger documented evidence architecture was identified in the existing manager artifacts, so neither is ranked as an active candidate.

Serious candidates:

1. FTSE TWSE Taiwan 50
2. Nifty 50
3. Nikkei 225
4. STOXX Europe 600
5. CSI 300

Hang Seng Index remains below the top five because the prior architecture classified it as conversion/workbench with materially weaker identity/instrument readiness and no strong current source-freeze evidence comparable to Taiwan.

## 6. Evidence-adjusted candidate assessment

### Candidate 1 — FTSE TWSE Taiwan 50

Existing repository evidence is materially stronger than for the other remaining populations:

- population boundary already explicit: `TW_TW50 / FTSE TWSE Taiwan 50`;
- 50 workbench rows and 49 historical Strict rows;
- source lineage `SRC_FTSE_TW50_CW_20260630` with source As-of 2026-06-30;
- source-authority carryforward records 50 source rows for the 50-row segment;
- identity-quality audit records 47/50 rows already satisfying strict `ISIN + Primary_MIC + Primary_Ticker` identity, only 3 fallback MIC+ticker+WS_ID rows and 3 missing ISINs;
- XTAI is the documented Primary MIC and the existing rows are marked ACTIVE_VERIFIED in the workbench lineage;
- single-market structure substantially reduces multi-MIC and cross-listing complexity.

This does not mean Taiwan is admission-ready. It means a policy gate has unusually strong existing evidence to work from without first inventing or hunting a new source architecture.

### Candidate 2 — Nifty 50

Positive evidence:

- exact 50-row institutional population boundary;
- single primary-market policy target `XNSE` in architecture;
- identity-quality audit shows 50/50 rows with strict ISIN+MIC+ticker identity and no missing ISINs;
- 45 historical Strict rows.

Main weakness: source-authority audit/carryforward did not show a fully materialized current 50-row official source snapshot in the same way Taiwan did; the segment was still flagged for explicit source-evidence freeze/audit. NSE/BSE dual-market questions also require policy handling. Thus identity is strong but population-evidence reproducibility is more conditional than Taiwan.

### Candidate 3 — Nikkei 225

Positive evidence:

- exact institutional 225-row boundary;
- 225 source rows documented for `SRC_NIKKEI225`;
- 197 historical Strict rows;
- single-primary-market architecture `XTKS`.

Main weakness: identity-quality audit records 225/225 missing ISIN and fallback MIC+ticker+WS_ID identity. This recreates a systematic Security-Level ISIN gap analogous in shape, though not evidence detail, to Brazil and therefore raises failure-loop risk materially.

### Candidate 4 — STOXX Europe 600

Positive evidence:

- exact institutional 600-row boundary;
- 600 workbench/source rows documented;
- large strategic and diversification gain.

Main weakness: identity-quality audit records 600/600 missing ISIN under current lineage, while the architecture spans many Primary MICs across countries. Primary-listing resolution, share-class selection and cross-listing controls are therefore considerably more complex than Taiwan/India/Japan. A policy gate is possible, but evidence-adjusted expected cost is higher.

### Candidate 5 — CSI 300

Positive evidence:

- exact 300-row institutional boundary;
- 300 source rows documented;
- 294 historical Strict rows;
- established XSHG/XSHE architecture.

Main weakness: identity-quality audit records 300/300 missing ISIN. Two-exchange A-share architecture plus A/H-share and cross-market identity risk create higher policy/identity complexity than Taiwan and India.

## 7. Evaluation matrix

| Dimension | Taiwan 50 | Nifty 50 | Nikkei 225 | STOXX Europe 600 | CSI 300 |
|---|---|---|---|---|---|
| Strategic Coverage Gain | MEDIUM | MEDIUM | HIGH | HIGH | HIGH |
| Diversification Gain | HIGH | HIGH | HIGH | HIGH | HIGH |
| Population Boundary Clarity | HIGH | HIGH | HIGH | HIGH | HIGH |
| Population Evidence Availability | STRONG | CONDITIONAL | STRONG | CONDITIONAL | STRONG |
| Security-Level Snapshot Reproducibility | STRONG | CONDITIONAL | CONDITIONAL | CONDITIONAL | CONDITIONAL |
| Primary Listing Evidence | STRONG | CONDITIONAL | STRONG | CONDITIONAL | CONDITIONAL |
| Security Identity Architecture | STRONG | STRONG | CONDITIONAL | CONDITIONAL | CONDITIONAL |
| ISIN Architecture | STRONG | STRONG | WEAK | WEAK | WEAK |
| Instrument Classification | STRONG | STRONG | STRONG | CONDITIONAL | CONDITIONAL |
| Share-Class Complexity | LOW | LOW | LOW | MEDIUM | MEDIUM |
| Cross-Listing Risk | LOW | MEDIUM | LOW | HIGH | HIGH |
| Corporate-Action Risk | LOW | MEDIUM | MEDIUM | MEDIUM | MEDIUM |
| Expected Admission Yield | HIGH | HIGH | MEDIUM | MEDIUM | MEDIUM |
| Expected Manual Cost | LOW | MEDIUM | MEDIUM | HIGH | HIGH |
| Scalability | YES | YES | LIMITED | LIMITED | LIMITED |
| Overlap Risk | LOW | LOW | LOW | MEDIUM | MEDIUM |
| Canada Failure-Mode Risk | LOW | LOW | MEDIUM | HIGH | HIGH |
| Korea Failure-Mode Risk | LOW | LOW | MEDIUM | MEDIUM | MEDIUM |
| US-3 Failure-Mode Risk | LOW | MEDIUM | MEDIUM | MEDIUM | MEDIUM |
| Brazil Failure-Mode Risk | LOW | MEDIUM | HIGH | HIGH | HIGH |
| Overall Failure-Loop Risk | LOW | MEDIUM | MEDIUM | HIGH | HIGH |
| Expected Information Value | HIGH | HIGH | MEDIUM | MEDIUM | MEDIUM |
| Overall Priority | HIGH | MEDIUM | MEDIUM | LOW | LOW |

## 8. Hard-exclusion review

- Taiwan 50: no hard exclusion triggered.
- Nifty 50: no hard exclusion triggered, but source-evidence reproducibility remains conditional, so it ranks behind Taiwan.
- Nikkei 225: ISIN architecture is WEAK under current repository identity evidence; therefore it cannot be #1.
- STOXX Europe 600: current ISIN architecture is WEAK and multi-market failure-loop risk is HIGH; therefore it cannot be #1.
- CSI 300: current ISIN architecture is WEAK and cross-market failure-loop risk is HIGH; therefore it cannot be #1.

Hong Kong is not promoted into the ranked five because prior evidence is weaker still for instrument/identity conversion. No concrete disjoint AU-2 or further US population with a superior documented evidence path is available in the reviewed governance artifacts.

## 9. Consolidate-first assessment

**Consolidate First: NO.**

The four parked populations show that indiscriminate expansion must stop when evidence becomes fragile. However Taiwan is materially different: the repository already contains a bounded 50-row institutional population, a 50-row documented source lineage, XTAI primary-market context, and 47/50 strict canonical identity tuples with only three ISIN gaps. This is sufficient to justify one policy-only stage without any source hunt or build.

## 10. Recommendation

**Recommendation: A**

**Decision: AUTHORIZE NEXT POPULATION POLICY GATE**

### Selected Next Population

**FTSE TWSE Taiwan 50**

### Exact Population Boundary

The exact 50-security `TW_TW50 / FTSE TWSE Taiwan 50` population already represented in the repository source/workbench lineage `SRC_FTSE_TW50_CW_20260630`; no broader Taiwan market, OTC population, free-form Taiwan list or foreign secondary listing is included.

### Primary Market / MIC Scope

**Taiwan Stock Exchange / XTAI** for the concrete local primary security. Any secondary/foreign representation must later fail closed unless explicitly proven to be the canonical primary security under policy.

### Expected Evidence Architecture

Reuse the existing repository architecture rather than discover a new one: named FTSE TWSE Taiwan 50 population lineage with 50/50 source-row coverage, XTAI primary-market codes, exact local security codes/tickers, security names, existing security-level ISINs for 47 rows, and the canonical identity model `ISIN + Primary_MIC + Primary_Ticker + exact Security Name + exact Share Class`. The policy gate must define handling for the three current ISIN-gap rows, instrument/share-class rules, source-currentness requirements and collision/corporate-action controls; it may not search for or materialize new evidence.

### Primary rationale

Taiwan has the best evidence-adjusted expected integration value among the remaining documented populations. Unlike Japan, Europe and China, it does not begin with a population-wide ISIN gap; unlike India, the repository already records a complete 50-row source lineage in addition to strong identity. Its single-market XTAI architecture, 47/50 strict identity coverage and 49/50 historical Strict coverage make the next policy gate both bounded and high-information while keeping failure-loop risk LOW.

## 11. Exact next authorized stage

**FTSE TWSE Taiwan 50 Admission Policy Gate — READ-ONLY**

Policy only. No source hunt, population snapshot, candidate build, admission or Universe write is authorized.

## 12. No-touch confirmation

Research Partial, Membership, Universe, Strict, Frozen, US-1, US-2, US-3, AU-1, Canada, Korea and Brazil were not changed. No mapping, history, liquidity, eligibility, scan/U3K or productive v7.2 work was performed. No follow-on stage was executed.

## 13. Quality gates G0-G17

- G0 Correct origin/main HEAD — PASS
- G1 Correct Post-Brazil Manager stage — PASS
- G2 Research Partial 2527 verified — PASS
- G3 Strict 759 verified — PASS
- G4 Frozen 0 verified — PASS
- G5 Canada remains PARKED — PASS
- G6 Korea remains PARKED — PASS
- G7 US-3 remains PARKED — PASS
- G8 Brazil remains PARKED — PASS
- G9 All four failure modes incorporated — PASS
- G10 Candidate set only from existing repo/governance evidence — PASS
- G11 No source hunt — PASS
- G12 Evaluation matrix completed — PASS
- G13 Hard exclusions applied — PASS
- G14 Consolidate First explicitly decided — PASS
- G15 Exactly one Recommendation A/B — PASS
- G16 Exact next authorized stage defined — PASS
- G17 No data/universe/follow-on change — PASS

**G0-G17: PASS**

## 14. Final state

**POST-BRAZIL NEXT-POPULATION MANAGER GATE — PASS**

**RECOMMENDATION A — AUTHORIZE NEXT POPULATION POLICY GATE**

**SELECTED NEXT POPULATION: FTSE TWSE Taiwan 50**

**NEXT AUTHORIZED STAGE: FTSE TWSE Taiwan 50 Admission Policy Gate — READ-ONLY**

HARD STOP.