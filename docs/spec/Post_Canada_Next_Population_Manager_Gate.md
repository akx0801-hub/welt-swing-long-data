# Post-Canada Next-Population Manager Gate

## Decision

**POST-CANADA NEXT-POPULATION MANAGER GATE — PASS**

**RECOMMENDATION A — KOREA**

**NEXT AUTHORIZED STAGE: Korea Admission Policy Gate — READ-ONLY**

This is a prioritization decision only. It authorizes no build, download, candidate generation, admission, integration, Universe write or Canada reactivation.

## Start and authorized stage

- Repository: akx0801-hub/welt-swing-long-data
- Branch: main
- Start HEAD: `7c59033e96ad0f4588348bb03fadd2c2830b755a`
- Authorized stage: Post-Canada Next-Population Manager Gate — READ-ONLY
- origin/main at startcheck: `7c59033e96ad0f4588348bb03fadd2c2830b755a`
- No completed duplicate of this exact gate was present.

## Governance and verified baseline

| Measure | Value |
|---|---:|
| Research Partial | 2527 |
| Strict | 759 |
| Frozen | 0 |
| Integrated US-1 | 372 |
| Integrated US-2 | 369 |
| Integrated US total | 741 |
| Integrated AU-1 | 153 |
| Canada Legacy | 217 retained / unchanged |
| Canada Rebuild | 217 retained |
| Canada ADMIT / REVIEW / EXCLUDE | 0 / 215 / 2 |
| Canada state | PARKED |

Welt-Swing v7.2 remains the only productive Trading Authority. DEV remains DEV / Research / Shadow. Membership, Eligibility, Scan and Execution remain separate layers. Identity remains ISIN + Primary_MIC + Primary_Ticker plus exact Security/Class evidence. Alpha Vantage is prohibited.

## Current regional coverage

The current auditable coverage is reconstructed transparently from the P6 regional snapshot (2,374 rows) plus the separately audited AU-1 addition of 153 rows:

| Region / market | Membership | Interpretation |
|---|---:|---|
| Americas / North America | 958 | US 741 + Canada 217; Canada is parked |
| Europe | 600 | substantial existing base; 137 Strict in the P6 snapshot |
| Asia-Pacific | 718 | Japan, China, Taiwan, India and Hong Kong represented; Korea 0 |
| Oceania / Australia | 153 | AU-1 integrated; no clean disjoint AU-2 scope defined |
| Other | 98 | Brazil / B3 block |
| Total | 2527 | Research Partial total |

Country-/market-level reference points in the current P5/P6 evidence include US 741, Canada 217, Japan 225, China 300, Taiwan 50, India 50, Hong Kong 93, Brazil 98, Australia 153 and Korea 0. The regional source artifacts are historical coverage evidence, not a new build input.

## Coverage gap analysis

- Quantitative gap: Korea has zero current membership in the Research Partial, while US and Asia-Pacific already have substantial blocks.
- Strategic gap: Korea would add a distinct developed Asian market and reduce dependence on the existing US-heavy North-American block.
- Already sufficiently represented: US has 741 integrated rows; further US breadth is not the most valuable next geographic step.
- Technically difficult: Korea has local market-code, class, preferred/common and identifier issues; the official KRX endpoint has previously returned an error.
- High additional value: Korea is the only evaluated zero-coverage developed-market direction with a plausible official market-data route and meaningful diversification value.

Canada remains parked and is not part of this expansion decision.

## Canada lessons applied

The Canada sequence demonstrated that population membership and ticker/MIC lineage do not establish admission identity. A future population must pass a pre-build feasibility check for:

- reproducible membership evidence;
- current primary listing and MIC;
- exact Security and Share Class;
- ISIN with semantic match;
- instrument type;
- corporate-action and collision controls.

A Korea Policy Gate is therefore required before any Korea Build. No Korea candidate list or instrument admission policy is created here.

## Option evaluation

### Korea

- Strategic Coverage: HIGH — zero current coverage and meaningful developed-market exposure.
- Diversification: HIGH — adds a distinct Asian market beyond the existing Japan/China/Taiwan/India/Hong Kong coverage.
- Expected Admission Yield: MEDIUM — plausible common-equity scope, but not yet proven.
- Identity Evidence: CONDITIONAL — official KRX route exists, but row-level identity/class/ISIN capability requires policy validation.
- Population Evidence: CONDITIONAL — KOSPI 200 is a concrete candidate population; the last official endpoint materialization returned an endpoint error.
- Listing Evidence: CONDITIONAL — KRX primary-market route is identifiable; current listing/MIC handling must be defined.
- ISIN Feasibility: CONDITIONAL — must be proven at Security/Class level; no fallback is permitted.
- Instrument/Class Complexity: HIGH — local codes, preferreds, multiple classes and foreign structures require explicit treatment.
- Corporate-Action Complexity: MEDIUM.
- Manual Cost: HIGH.
- Scalability: LIMITED until the official KRX access and identity route is validated.
- Collision Risk: MEDIUM.
- Canada-failure-mode risk: MEDIUM/HIGH if a Policy Gate is skipped; controlled by the required pre-build feasibility gate.
- Overall Priority: HIGH.

### AU-2

- Strategic Coverage: LOW/MEDIUM — Australia already has 153 AU-1 integrations.
- Diversification: LOW — adds depth within an existing market.
- Expected Admission Yield: LOW/MEDIUM — no clean disjoint source population is currently defined.
- Identity Evidence: CONDITIONAL — AU-1 proved a clean ASX-200 Common/Ordinary path, but not a new AU-2 scope.
- Population Evidence: WEAK for a disjoint AU-2 population.
- Listing Evidence: CONDITIONAL.
- ISIN Feasibility: CONDITIONAL.
- Instrument/Class Complexity: HIGH in the likely residual universe.
- Manual Cost: HIGH.
- Scalability: NO/LIMITED.
- Collision Risk: HIGH because reopening AU-1 review/exclude/residual rows would create overlap risk.
- Canada-failure-mode risk: MEDIUM.
- Overall Priority: LOW.

AU-2 is not recommended. Reworking AU-1 residuals would not constitute a clean new population.

### US-3

- Strategic Coverage: MEDIUM — adds US breadth.
- Diversification: LOW — increases an already dominant 741-row US block.
- Expected Admission Yield: HIGH — US-1 and US-2 provide a proven evidence and integration pattern.
- Identity Evidence: STRONG.
- Population Evidence: STRONG/CONDITIONAL depending on the future disjoint index scope.
- Listing Evidence: STRONG.
- ISIN Feasibility: STRONG.
- Instrument/Class Complexity: LOW/MEDIUM for a Common-only policy.
- Manual Cost: LOW/MEDIUM.
- Scalability: YES.
- Collision Risk: MEDIUM because a disjoint scope and overlap controls are still required.
- Canada-failure-mode risk: LOW.
- Overall Priority: LOW for the next global expansion because the marginal geographic value is limited.

US-3 is technically attractive but not the best next global coverage decision.

### OTHER / alternative population

No other concrete market currently dominates Korea on the combined criteria. Europe is already broad; Japan, China, Taiwan, India, Hong Kong and Brazil have existing coverage; Australia is covered by AU-1. No new Other population is recommended.

- Overall Priority: NONE.
- No alternative population was started.

### Consolidate First

Consolidation first is not selected. The current audits establish a coherent 2,527-row Research Partial, AU-1 integrity passed, US-1/US-2 integrity passed, Strict remains a separate dry-run, and Frozen remains zero. There is no identified consolidation blocker that objectively outweighs the strategic value of a controlled Korea Policy Gate.

## Pre-build evidence feasibility matrix

| Option | Population | Security identity | Current listing | ISIN | Instrument/Class |
|---|---|---|---|---|---|
| Korea / KOSPI 200 candidate | CONDITIONAL | CONDITIONAL | CONDITIONAL | CONDITIONAL | CONDITIONAL |
| AU-2 | WEAK | CONDITIONAL | CONDITIONAL | CONDITIONAL | WEAK |
| US-3 | STRONG/CONDITIONAL | STRONG | STRONG | STRONG | STRONG |
| Other | WEAK | WEAK | WEAK | WEAK | WEAK |
| Consolidate | N/A | N/A | N/A | N/A | N/A |

The Korea recommendation does not mean Korea is build-ready. It means Korea is the best next subject for a dedicated Admission Policy Gate that must resolve the conditional evidence questions before any build.

## Opportunity-cost matrix

| Option | Coverage gain | Diversification | Evidence feasibility | Expected yield | Cost | Scalability | Failure risk | Decision |
|---|---|---|---|---|---|---|---|---|
| Korea | High | High | Conditional | Medium | High | Limited | Medium/High | Recommend |
| AU-2 | Low/Medium | Low | Weak | Low/Medium | High | Limited | Medium | Reject |
| US-3 | Medium | Low | Strong | High | Low/Medium | Yes | Low | Defer |
| Other | Unclear | Unclear | Weak | Unclear | High | Unclear | High | Reject |
| Consolidate | No new coverage | None | N/A | N/A | Medium | N/A | Low | Not needed |

## Final recommendation

**RECOMMENDATION A — KOREA**

**Decision: KOREA**

Korea offers the strongest marginal global coverage and diversification value after Canada was parked. The decision is deliberately policy-first: the official KRX path has a documented technical limitation, so the next authorized stage is only:

**Korea Admission Policy Gate — READ-ONLY**

No Korea build is authorized by this report.

## Quality gates

- G0 Correct origin/main HEAD — PASS
- G1 Correct authorized Manager stage — PASS
- G2 Canada PARKED recognized — PASS
- G3 Research Partial 2527 verified — PASS
- G4 Strict 759 / Frozen 0 verified — PASS
- G5 US-1 / US-2 / AU-1 state verified — PASS
- G6 Current regional coverage evaluated — PASS
- G7 Coverage gaps evaluated — PASS
- G8 Canada lessons applied — PASS
- G9 Korea evaluated — PASS
- G10 AU-2 evaluated — PASS
- G11 US-3 evaluated — PASS
- G12 Other evaluated — PASS
- G13 Consolidate-first evaluated — PASS
- G14 Evidence feasibility compared — PASS
- G15 Exactly one recommendation selected — PASS
- G16 No Universe/Data write — PASS
- G17 No follow-on stage executed — PASS

## No-touch confirmation

No candidate was downloaded or generated. No build, admission, integration, mapping, history, liquidity, eligibility, scan, U3K freeze or Canada reactivation was performed. Research Partial remains 2527; Strict remains 759; Frozen remains 0. Canada Legacy 217, Canada Rebuild 217, US-1 372, US-2 369 and AU-1 153 remain unchanged.

**POST-CANADA NEXT-POPULATION MANAGER GATE — PASS**

**RECOMMENDATION A — KOREA**
