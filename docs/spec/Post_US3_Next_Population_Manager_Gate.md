# Post-US3 Next-Population Manager Gate

## Stage decision

**POST-US3 NEXT-POPULATION MANAGER GATE — PASS**

**RECOMMENDATION A — AUTHORIZE NEXT POPULATION POLICY GATE**

**SELECTED NEXT POPULATION: Brazil — IBrX 100**

**NEXT AUTHORIZED STAGE: Brazil IBrX 100 Admission Policy Gate — READ-ONLY**

This is a read-only manager decision. It performs no source hunt, no population materialization, no candidate generation, no admission, no build, no mapping/history/liquidity/eligibility/scan work, no Frozen write and no Universe/Research-Partial/Membership write.

## 1. Start HEAD and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `82de7bc85e6b26b40d5f42150b453ad4912c6f95`
- origin/main at startcheck: `82de7bc85e6b26b40d5f42150b453ad4912c6f95`
- Verified predecessor commit: `US-3 named-index tracker qualification gate`
- Authorized stage: **Post-US3 Next-Population Manager Gate — READ-ONLY**
- No newer manager decision existed at startcheck.

Actual repository references used include:

- `docs/spec/US3_Named_Index_Tracker_Qualification_Gate.md`
- `docs/spec/US3_Population_Evidence_Manager_Gate.md`
- `docs/spec/US3_Population_Evidence_Validation_Gate.md`
- `docs/spec/US3_Admission_Policy_Gate.md`
- `docs/spec/Post_Korea_Next_Population_Manager_Gate.md`
- `docs/spec/Post_Canada_Next_Population_Manager_Gate.md`
- `docs/spec/US2_Admission_Policy_ReadOnly.md`
- `docs/spec/US2_SP400_Admission_Build_Report.md`
- `docs/spec/US1_Integration_Evidence_Gate_Report.md`
- `docs/spec/Post_Integration_Integrity_Audit_US1_US2.md`
- `docs/spec/P5_0_Architecture_Coverage_Gate.md`
- `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
- `WELT-SWING-CURRENT-Handoff-v0.22.md`
- `WELT-SWING-CURRENT-Handoff-v0.23.md`
- `WELT-SWING-CURRENT-Handoff-v0.30.md`
- `docs/validation/Current_Master_Materialized_Official_Membership_Identity_Reconciliation_v0.31.md`

Where requested filenames did not exist exactly, the repository-equivalent artifact was used. No file or source was invented.

## 2. Governance and baseline

WELT-SWING LONG DEV remains **DEV / RESEARCH / SHADOW**. Welt-Swing v7.2 remains the **SOLE PRODUCTIVE AUTHORITY**. Membership ≠ Identity ≠ Eligibility ≠ Scan ≠ Execution. Alpha Vantage remains prohibited.

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
| U3K Frozen Membership | 0 |

Research Partial 2527 is a workbench/research state, not productive U3K membership. Strict 759 is an Eligibility Dry-Run, not a membership tier. Frozen remains 0.

## 3. Canada lesson

Canada remains **PARKED**. The relevant lesson is that attractive population coverage is insufficient when exact Security/Class identity, ISIN and reproducible admission evidence require repeated manual recovery. Repeated zero-ready outcomes showed that membership availability without scalable canonical identity is not enough.

Manager consequence for this gate: candidates with expected security-by-security recovery, weak reproducibility or HIGH failure-loop risk cannot rank first.

## 4. Korea lesson

Korea remains **PARKED**. The documented KOSPI 200 path failed on reproducible official population/listing/identity access and produced 0/12 READY in the validation sequence. Source scalability was NO.

Manager consequence: a clear institutional index name alone is insufficient. Population evidence, listing evidence and identity architecture must all be practically reproducible.

## 5. US-3 lesson

US-3 remains **PARKED** under the current governance input. Its population boundary, listing architecture, Security identity architecture, ISIN controls and R4 methodology were strong, and the IJR named-index tracker qualification passed. The subsequent v2 population-evidence execution nevertheless failed at the required reproducible raw-materialization/sealing step and was stopped under the one-path rule.

Manager consequence: theoretical or browser-level source availability is not enough. The next population should preferably already have repository evidence of successful machine-materialized current membership at Security level.

## 6. Existing integrated and Research-Partial coverage

The current 2527-row Research Partial is reconstructed from the existing manager artifacts as:

| Market/region | Rows | Current interpretation |
|---|---:|---|
| US | 741 | integrated US-1/US-2 |
| Canada | 217 | workbench / parked |
| Brazil | 98 | workbench / official membership evidence exists |
| Europe | 600 | workbench / conversion candidate |
| Japan | 225 | workbench / historically high Strict coverage |
| China | 300 | workbench / historically high Strict coverage |
| Taiwan | 50 | workbench / historically high Strict coverage |
| India | 50 | workbench / historically high Strict coverage |
| Hong Kong | 93 | workbench / unresolved instrument evidence in historical audits |
| Australia | 153 | integrated AU-1 |
| Korea | 0 | parked |
| Total | 2527 | Research Partial |

The directly documented integrated expansion rows remain 741 US + 153 AU-1 = **894**.

## 7. Candidate set

Only repository-grounded candidates were evaluated. Canada, Korea and US-3 are excluded from reactivation. AU-2 remains without a clean disjoint population in the existing manager evidence. No new source or provider was searched.

Serious candidates retained for ranking:

1. **Brazil — IBrX 100**
2. **Japan — Nikkei 225**
3. **Europe — STOXX Europe 600**
4. **Taiwan — FTSE TWSE Taiwan 50**
5. **India — Nifty 50**

China was evaluated but not ranked in the top five because its cross-market/share-structure and foreign-listing complexity creates higher policy and identity risk despite strong historical workbench coverage. Hong Kong remains less attractive because prior repository audits documented 82 unresolved instrument rows out of 93. AU-2 remains structurally weak and overlap-prone. Further US expansion after parked US-3 has low diversification benefit and no documented population with a clearly better materialization path than the failed US-3 route.

## 8. Candidate evaluation matrix

### Candidate 1 — Brazil / IBrX 100

**Exact candidate boundary:** current official B3 IBrX 100 portfolio, Security-level B3 codes, with later policy restricted to ordinary/common-equity securities and fail-closed treatment of preferreds, units and unresolved instruments.

Repository evidence is materially stronger than for the other remaining candidates:

- v0.30: `MATERIALIZED_OFFICIAL_B3_CURRENT_MEMBERSHIP_EVIDENCE`
- official rows: 98
- unique Security codes: 98
- canonical import: false
- v0.31: official B3 header date 31/08/26; Primary MIC `BVMF`; deterministic B3 instrument semantics for ON vs PN/UNIT; no guessed ISIN; identity/import still separately gated.

| Dimension | Assessment |
|---|---|
| Strategic Coverage Gain | MEDIUM |
| Diversification Gain | HIGH |
| Population Boundary Clarity | HIGH |
| Population Evidence Availability | STRONG |
| Security-Level Snapshot Reproducibility | STRONG |
| Listing Evidence | STRONG |
| Security Identity Architecture | CONDITIONAL |
| ISIN Architecture | CONDITIONAL |
| Instrument Classification | STRONG |
| Expected Admission Yield | MEDIUM |
| Expected Manual Cost | LOW/MEDIUM |
| Scalability | YES |
| Overlap Risk | LOW |
| Corporate-Action Risk | MEDIUM |
| Canada/Korea/US3 Failure-Mode Risk | LOW |
| Expected Information Value | HIGH |
| Overall Priority | HIGH |

Interpretation: Brazil has the most important property missing in the three parked cases — a repository-demonstrated, current official Security-level membership materialization path that has already succeeded in batch form. The remaining weaknesses are policy/identity adjudication, not population-source discovery.

### Candidate 2 — Japan / Nikkei 225

Historical repository audits show 225 source rows and 207 Strict in the v0.23 lineage, indicating mature data/instrument handling relative to most markets. However this manager gate found no equivalently recent repository proof of a current official Security-level membership materialization comparable to B3 v0.30.

| Dimension | Assessment |
|---|---|
| Strategic Coverage Gain | MEDIUM |
| Diversification Gain | HIGH |
| Population Boundary Clarity | HIGH |
| Population Evidence Availability | CONDITIONAL |
| Security-Level Snapshot Reproducibility | CONDITIONAL |
| Listing Evidence | STRONG |
| Security Identity Architecture | CONDITIONAL/STRONG |
| ISIN Architecture | CONDITIONAL |
| Instrument Classification | STRONG |
| Expected Admission Yield | HIGH |
| Expected Manual Cost | MEDIUM |
| Scalability | LIMITED/YES |
| Overlap Risk | LOW |
| Corporate-Action Risk | MEDIUM |
| Canada/Korea/US3 Failure-Mode Risk | MEDIUM |
| Expected Information Value | HIGH |
| Overall Priority | MEDIUM |

Japan remains a strong future candidate but does not outrank Brazil because current-source materialization evidence is less directly proven in the artifacts reviewed.

### Candidate 3 — Europe / STOXX Europe 600

Europe has 600 source-lineage rows. v0.22/v0.23 show that the population is present and reconciled, but 365 rows historically remained instrument-unresolved; 227 were valid liquidity exclusions and 8 were data-history candidates. Europe therefore has strong strategic breadth but a substantial multi-market instrument/identity remediation burden.

| Dimension | Assessment |
|---|---|
| Strategic Coverage Gain | HIGH |
| Diversification Gain | HIGH |
| Population Boundary Clarity | HIGH |
| Population Evidence Availability | CONDITIONAL |
| Security-Level Snapshot Reproducibility | CONDITIONAL |
| Listing Evidence | CONDITIONAL |
| Security Identity Architecture | CONDITIONAL |
| ISIN Architecture | CONDITIONAL/STRONG |
| Instrument Classification | WEAK/CONDITIONAL |
| Expected Admission Yield | MEDIUM |
| Expected Manual Cost | HIGH |
| Scalability | LIMITED |
| Overlap Risk | MEDIUM |
| Corporate-Action Risk | MEDIUM |
| Canada/Korea/US3 Failure-Mode Risk | MEDIUM |
| Expected Information Value | HIGH |
| Overall Priority | MEDIUM |

Europe is not excluded, but it is not the next best policy target while 365 historical instrument-evidence gaps remain a known bulk-remediation problem.

### Candidate 4 — Taiwan / FTSE TWSE Taiwan 50

Historical lineage shows 50/50 Strict, the strongest segment-level coverage result in v0.22. Population boundary is clear and the scope is small, but the incremental strategic coverage is limited because all 50 are already represented in the Research Partial workbench and no newer official-current source-materialization proof comparable to B3 v0.30 was identified in the reviewed artifacts.

| Dimension | Assessment |
|---|---|
| Strategic Coverage Gain | LOW |
| Diversification Gain | MEDIUM |
| Population Boundary Clarity | HIGH |
| Population Evidence Availability | CONDITIONAL |
| Security-Level Snapshot Reproducibility | CONDITIONAL |
| Listing Evidence | STRONG |
| Security Identity Architecture | STRONG |
| ISIN Architecture | CONDITIONAL |
| Instrument Classification | STRONG |
| Expected Admission Yield | HIGH |
| Expected Manual Cost | LOW |
| Scalability | YES/LIMITED |
| Overlap Risk | HIGH at workbench-conversion level |
| Corporate-Action Risk | LOW/MEDIUM |
| Canada/Korea/US3 Failure-Mode Risk | LOW/MEDIUM |
| Expected Information Value | MEDIUM |
| Overall Priority | MEDIUM |

### Candidate 5 — India / Nifty 50

Historical lineage shows 50 source rows and 45 Strict. The population is clear and compact, but like Taiwan the repository evidence reviewed here does not establish a newer official-current membership materialization path at the same evidence level as Brazil.

| Dimension | Assessment |
|---|---|
| Strategic Coverage Gain | LOW/MEDIUM |
| Diversification Gain | HIGH |
| Population Boundary Clarity | HIGH |
| Population Evidence Availability | CONDITIONAL |
| Security-Level Snapshot Reproducibility | CONDITIONAL |
| Listing Evidence | CONDITIONAL/STRONG |
| Security Identity Architecture | CONDITIONAL/STRONG |
| ISIN Architecture | CONDITIONAL |
| Instrument Classification | STRONG |
| Expected Admission Yield | HIGH |
| Expected Manual Cost | MEDIUM |
| Scalability | LIMITED/YES |
| Overlap Risk | HIGH at workbench-conversion level |
| Corporate-Action Risk | MEDIUM |
| Canada/Korea/US3 Failure-Mode Risk | MEDIUM |
| Expected Information Value | MEDIUM |
| Overall Priority | MEDIUM |

## 9. Other evaluated directions and hard exclusions

### Further US after US-3

Not selected. US already has 741 integrated rows and the most recently tested additional bounded S&P population ended parked on reproducible materialization. No repository-documented further US population was shown to have a demonstrably better current population-evidence path. Recommending another US segment now would risk repeating the same evidence failure while adding little geographic diversification.

### AU-2

Not selected. Existing manager gates explicitly found no clean disjoint AU-2 population. Reopening AU-1 review/exclude residuals would create overlap and instrument-complexity risk rather than a clean new population.

### China / CSI 300

Historical coverage is strong (300 source / 295 Strict), but share structures, exchange scope and foreign/secondary-listing ambiguity make a new policy conversion more complex than Brazil. Current official materialization evidence comparable to B3 was not established in the artifacts used for this decision. Not top five under the evidence-adjusted rule.

### Hong Kong / Hang Seng Index

93 workbench rows exist, but historical v0.23 evidence showed 82 instrument-unresolved rows. This creates a known remediation burden and a higher failure-mode risk than Brazil/Japan/Taiwan/India.

### Consolidate first

**Consolidate First: NO.**

The three latest parked paths demonstrate a need for stricter source selection, not a general expansion freeze. Brazil is materially different because an official, current, full Security-level population was already successfully machine-materialized and uniquely counted before this manager stage. This directly satisfies the central evidence lesson from Canada/Korea/US-3. Therefore a policy-only Brazil gate has higher expected information value than stopping expansion now.

## 10. Ranking

| Rank | Candidate | Primary advantage | Primary risk | Overall Priority |
|---:|---|---|---|---|
| 1 | Brazil — IBrX 100 | Official B3 current membership already materialized: 98/98 unique Security codes; BVMF and instrument semantics documented | ISIN/identity completion still policy-gated | HIGH |
| 2 | Japan — Nikkei 225 | Mature workbench lineage, 207/225 historical Strict, single-market structure | Current official population materialization not comparably proven here | MEDIUM |
| 3 | Europe — STOXX Europe 600 | Large diversification benefit and 600-row source lineage | 365 historical instrument-unresolved rows; multi-market MIC complexity | MEDIUM |
| 4 | Taiwan — FTSE TWSE Taiwan 50 | 50/50 historical Strict, compact and mature | Small incremental coverage; current materialization evidence not re-proven | MEDIUM |
| 5 | India — Nifty 50 | 45/50 historical Strict and high diversification value | Current source/ISIN path only conditional in reviewed evidence | MEDIUM |

## 11. Hard-exclusion review

Brazil passes the manager minimum for Option A:

- Population Boundary Clarity: HIGH
- Population Evidence Availability: STRONG
- Security-Level Snapshot Reproducibility: STRONG
- Listing Evidence: STRONG
- Security Identity Architecture: CONDITIONAL but explicitly structured and batch-oriented
- ISIN Architecture: CONDITIONAL; no guessed ISIN allowed and fallback governance already documented
- Expected Admission Yield: MEDIUM
- Scalability: YES
- Failure-Mode Risk: LOW
- Expected Information Value: HIGH

No hard-exclusion condition applies to Brazil. The next stage must remain policy-only and must not treat the previous v0.31 identity candidates as already admitted.

## 12. Recommendation

**RECOMMENDATION A — AUTHORIZE NEXT POPULATION POLICY GATE**

**Selected Next Population: Brazil — IBrX 100**

**Exact Population Boundary:** current official B3 IBrX 100 Security-level portfolio; later admission policy restricted to primary B3/BVMF ordinary/common equities, with preferreds, units and unresolved instrument types fail-closed unless the policy explicitly defines otherwise.

**Primary Market / MIC Scope:** Brazil — B3, Primary MIC `BVMF`.

**Expected Evidence Architecture:** reuse the already materialized official B3 `GetPortfolioDay` current-membership path (98 rows / 98 unique Security codes), BVMF primary-market rule and deterministic B3 instrument semantics documented in v0.30/v0.31; then formalize exact identity/ISIN/share-class/corporate-action/collision rules before any build.

Primary reason: Brazil is the only remaining documented candidate with an already successful official current Security-level population materialization in the repository. It therefore has the best evidence-adjusted probability of avoiding the Canada/Korea/US-3 source loop while adding meaningful non-US diversification.

## 13. Exact next authorized stage

**NEXT AUTHORIZED STAGE: Brazil IBrX 100 Admission Policy Gate — READ-ONLY**

This does not authorize a Brazil build, evidence acquisition run, source hunt, candidate generation, admission, mapping, history, liquidity, eligibility, integration or Universe write.

## 14. No-touch confirmation

No new source was tested. No population snapshot, evidence sidecar, candidate population or admission output was created. Canada, Korea and US-3 were not reactivated. US-1, US-2 and AU-1 were unchanged. Research Partial remains 2527. Strict remains 759. Frozen remains 0. No Membership, Universe/Data Master, Mapping, History, Liquidity, Eligibility, Scan/U3K or productive v7.2 artifact was changed.

## 15. Quality gates G0-G17

- G0 Correct origin/main HEAD — PASS
- G1 Correct Post-US3 manager stage — PASS
- G2 Research Partial 2527 verified — PASS
- G3 Strict 759 verified — PASS
- G4 Frozen 0 verified — PASS
- G5 Canada PARKED retained — PASS
- G6 Korea PARKED retained — PASS
- G7 US-3 PARKED retained — PASS
- G8 US-3 materialization failure correctly incorporated — PASS
- G9 Existing 894 integrated expansion rows recognized — PASS
- G10 Candidate set based only on existing repo/governance evidence — PASS
- G11 No source hunt performed — PASS
- G12 Evaluation matrix completed — PASS
- G13 Hard-exclusion rules applied — PASS
- G14 Exactly one A/B recommendation — PASS
- G15 Exact next authorized stage defined — PASS
- G16 No data/universe change — PASS
- G17 No follow-on stage executed — PASS

**G0-G17: PASS**

## 16. Final state

**POST-US3 NEXT-POPULATION MANAGER GATE — PASS**

**RECOMMENDATION A — AUTHORIZE NEXT POPULATION POLICY GATE**

**SELECTED NEXT POPULATION: Brazil — IBrX 100**

**NEXT AUTHORIZED STAGE: Brazil IBrX 100 Admission Policy Gate — READ-ONLY**

HARD STOP.
