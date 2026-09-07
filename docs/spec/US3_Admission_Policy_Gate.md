# US-3 Admission Policy Gate

## Stage decision

**US-3 ADMISSION POLICY GATE — PASS**

**BUILD READINESS: READY WITH CONDITIONS**

**NEXT AUTHORIZED STAGE: US-3 Population Evidence Validation Gate — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

This is a policy-only gate. It authorizes no S&P SmallCap 600 download, source hunt, candidate generation, admission, build, integration, mapping, history, liquidity, eligibility, Strict/Frozen change, scan/U3K work or Universe/Research-Partial write.

## 1. Start HEAD and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `0bd02455bae8feaa488657f23771c1f1544c3f4c`
- origin/main at startcheck: `0bd02455bae8feaa488657f23771c1f1544c3f4c`
- Verified predecessor commit: `Post-Korea next population manager gate`
- Authorized stage: **US-3 Admission Policy Gate — READ-ONLY**
- No completed `docs/spec/US3_Admission_Policy_Gate.md` existed at startcheck.
- No newer origin/main decision was present at startcheck.

Actual predecessor/reference paths used:

- `docs/spec/Post_Korea_Next_Population_Manager_Gate.md`
- `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
- `docs/spec/P5_1_US_Primary_Admission_Readiness.md` — actual US-1 admission/readiness architecture reference
- `docs/spec/US1_Integration_Evidence_Gate_Report.md` — actual US-1 evidence/integration gate report
- `output_us1_write/summary_us1_write.json` and `output_us1_integrity_audit/summary_us1_integrity_audit.json` — actual US-1 controlled-write/integrity summaries referenced by repository search
- `docs/spec/US1_Manager_Gate_Next_Segment.md` — actual US-1 closure/manager reference
- `docs/spec/US2_Admission_Policy_ReadOnly.md`
- `docs/spec/US2_SP400_Admission_Build_Report.md`
- `output_us2_write/summary_us2_write.json` — actual US-2 controlled-write summary referenced by repository search
- `docs/spec/Post_Integration_Integrity_Audit_US1_US2.md`

Where an expected prose report name was not present exactly, the actual repository-equivalent artifact above is used; no filename is invented.

## 2. Governance and current state

WELT-SWING LONG DEV remains **DEV / RESEARCH / SHADOW**. Welt-Swing v7.2 remains the **SOLE PRODUCTIVE AUTHORITY**.

Membership ≠ Identity ≠ Eligibility ≠ Scan ≠ Execution.

Verified baseline carried forward:

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
| US-3 | NOT BUILT |
| US-3 Candidate Population | NOT MATERIALIZED |

Canonical Security Identity remains:

`ISIN + Primary_MIC + Primary_Ticker + exact Security Name + exact Share Class`

Prohibited identity shortcuts remain: ticker-only identity, issuer-only identity, CIK-only identity, CUSIP-as-ISIN, silent ISIN fallback, silent MIC merge, silent class merge and silent successor mapping.

Alpha Vantage remains prohibited.

## 3. Manager decision input

The predecessor Manager Gate selected **RECOMMENDATION A — US-3** with intended scope:

- S&P SmallCap 600
- Common / Ordinary
- Primary XNYS / XNAS
- disjoint at canonical-Security-row level from US-1 S&P 500 and US-2 S&P MidCap 400

The predecessor assessment was: Strategic Coverage Gain MEDIUM; Diversification LOW; Population Clarity HIGH; Population Evidence CONDITIONAL; Listing Evidence STRONG; Security Identity Evidence STRONG; ISIN Evidence STRONG; Expected Admission Yield HIGH; Scalability YES; Failure-Mode Risk LOW/MEDIUM; Overall Priority HIGH.

The central unresolved item is therefore not identity architecture but **current reproducible population evidence**.

## 4. US-3 population definition and boundary

**Target Index:** S&P SmallCap 600  
**Primary Market:** United States  
**Allowed Primary MICs:** `XNYS`, `XNAS`  
**Target Instrument:** current primary-listed Common / Ordinary Equity only, subject to the instrument matrix below.

No additional MIC is added. Existing US-1/US-2 architecture explicitly limits the bounded US-primary common path to XNYS/XNAS and excludes ARCX/BATS/IEX/OTC/Pink. No repository evidence reviewed in this gate establishes another MIC as required for the US-3 bounded scope.

US-3 is not “remaining US stocks”, not a free-form small-cap list and not a market-cap screen. It is a named S&P SmallCap 600 population whose current membership must be evidenced before build.

## 5. Disjointness definition

US-3 must be disjoint from US-1 and US-2 at the **canonical Security row** level.

Disjointness means no duplicate canonical Security row. It does not mean an issuer or Security may never have historically belonged to another S&P segment.

Current index membership is population evidence; canonical Security identity is persistent identity evidence. Index migration must never create a second Security row for an identity already present in Research Partial.

## 6. Population membership policy

A later US-3 candidate can claim **CURRENT S&P SMALLCAP 600 MEMBERSHIP** only from a documented, dated and reproducible population-evidence chain.

Membership must not be inferred solely from company size, small-cap label, market capitalization, an unprovenanced ticker list, search-engine results, Wikipedia alone, broker lists or screener classification.

Evidence hierarchy for US-3:

1. **R1 — official index/index-administrator evidence:** preferred population evidence where reproducibly materializable.
2. **R2 — official exchange/listing evidence:** strong for current primary listing and Security details, but not by itself proof of S&P SmallCap 600 membership unless it explicitly supplies that membership.
3. **R3 — issuer/regulatory/registry evidence:** strong for Security identity, share class, corporate actions and identifiers; membership only where the source explicitly evidences the index membership.
4. **R4 — institutional named-index tracker file:** conditionally acceptable as population-membership evidence in the successful US architecture only when all institutional-holdings requirements in section 8 are met; never a silent substitute for a missing provenance chain and never allowed to override conflicting higher-rank evidence.
5. **Secondary / discovery-only:** cross-check only; never sufficient alone for final membership.

This policy preserves the master Source-Gate: secondary lists and generic ETF holdings are not canonical replacement memberships. The only holdings route tolerated in the US admission architecture is a specifically qualified institutional **named-index** tracker snapshot with explicit provenance and controls.

## 7. Wikipedia policy

**Wikipedia Role: DISCOVERY / SECONDARY / SUPPORTING / NOT SUFFICIENT FOR FINAL MEMBERSHIP.**

US-1/US-2 evidence history shows Wikipedia was used as a secondary/discovery snapshot, while final admission required stronger evidence; US-2 explicitly recorded `Wiki-only admits 0`. Accordingly:

- Wikipedia may seed discovery or provide a secondary cross-check.
- Wikipedia may not independently establish current S&P SmallCap 600 membership.
- Wikipedia may not establish canonical Security identity, semantic ISIN, current primary listing or corporate-action clearance.
- Conflict with higher-rank evidence => REVIEW / fail closed.

## 8. Institutional holdings policy

The successful US-2 architecture accepted a named-index institutional tracker file at rank 4 (`iShares_IJH_SP400`) as membership evidence, with a dated snapshot, and explicitly admitted zero Wikipedia-only names.

For US-3, no new fund is selected in this stage. A later institutional tracker may qualify only if all of the following are demonstrated:

- unequivocal stated tracking relationship to **S&P SmallCap 600**;
- institutional provider;
- current downloadable snapshot, not a marketing page;
- Security-level holdings rows;
- reproducible retrieval/materialization;
- sufficient Security identifiers to reconcile each row without ticker-only identity;
- explicit As-of-Date;
- documented retrieval date and provenance;
- population completeness/coverage measurable from the file;
- no unresolved conflict with higher-rank membership or listing evidence.

**Institutional Holdings Role:** conditionally sufficient R4 membership evidence for a bounded US admission sidecar only after those requirements pass; supporting/cross-check evidence otherwise. It does not by itself authorize Universe write.

## 9. Population Evidence Hard Gate

Because predecessor Population Evidence = CONDITIONAL, this is a hard prerequisite.

Before any US-3 Candidate Admission or Admission Build can start, there must be a **reproducible current S&P SmallCap 600 population snapshot** that:

- unequivocally represents S&P SmallCap 600;
- has an As-of-Date;
- contains Security-level rows;
- is reproducibly materializable;
- has documented Source Rank and provenance;
- has measurable population completeness/coverage;
- provides enough identifiers to reconcile membership rows without free-form reconstruction.

If this cannot be proven: **FAIL CLOSED**. No assembled replacement list, Wikipedia-only population, broker list, screener list or opportunistic candidate set may substitute.

## 10. Instrument policy

| Instrument class | US-3 policy | Notes |
|---|---|---|
| Common Stock | POTENTIALLY ADMIT | only with all ADMIT requirements |
| Ordinary Share | POTENTIALLY ADMIT | only with all ADMIT requirements |
| Class A Common | POTENTIALLY ADMIT | Security-level class evidence required |
| Class B Common | POTENTIALLY ADMIT | Security-level class evidence required |
| Class C Common | POTENTIALLY ADMIT | Security-level class evidence required |
| REIT | REVIEW | continue US-2 fail-closed policy |
| BDC / LP / MLP | REVIEW | continue US-2 fail-closed policy |
| Preferred | REVIEW | discoverable but never default Common/Ordinary ADMIT; pref-only remains REVIEW |
| ADR / ADS / Depositary Receipt | EXCLUDE | US MIC does not convert a DR into US primary ordinary equity |
| ETF | EXCLUDE | prohibited instrument |
| Fund | EXCLUDE | prohibited instrument |
| Unit | EXCLUDE | prohibited instrument |
| Trust not qualifying as ordinary common | REVIEW / EXCLUDE | fail closed based on exact instrument structure |
| SPAC Common | EXCLUDE | continue explicit US-2 SPAC exclusion; no new reason to broaden policy |
| SPAC Unit | EXCLUDE | prohibited |
| SPAC Warrant | EXCLUDE | prohibited |
| Warrant | EXCLUDE | prohibited |
| Right | EXCLUDE | prohibited |
| Structured Product | EXCLUDE | prohibited |
| Foreign secondary listing | EXCLUDE | cannot be used as US-3 primary Security |
| Unknown instrument | REVIEW / EXCLUDE | never ADMIT while unresolved |

## 11. Common / Ordinary and share classes

Common/Ordinary is **POTENTIALLY ADMIT** only after current membership, current primary listing, exact identity, allowed instrument and collision gates pass.

Multiple Common-share classes of one issuer are distinct Securities and must be discovered/reconciled separately. No issuer-level identity may be copied across classes. If more than one class is legitimately within the population, each must first have exact class-specific evidence. A later canonical-scan-class decision may select one class per issuer x MIC under the existing DEV architecture; that selection must never silently merge identities.

Membership evidence naming Class A while identity evidence points to Class B/C => `IDENTITY_REVIEW`, never silent mapping.

## 12. REIT policy

**REIT: REVIEW.**

US-2 documented REIT/BDC/LP/MLP as fail-closed REVIEW, and the US-2 build kept REITs in REVIEW rather than ADMIT. No repository evidence in this gate supports broadening that rule. US-3 therefore continues the same treatment.

## 13. ADR / DR policy

**ADR / DR: EXCLUDE.**

A listing on XNYS/XNAS does not make an ADR/ADS the primary ordinary Security. No foreign primary Security may enter US-3 through its US depositary wrapper. Foreign secondary listings are likewise EXCLUDE.

## 14. SPAC policy

- **SPAC Common: EXCLUDE**
- **SPAC Unit: EXCLUDE**
- **SPAC Warrant: EXCLUDE**

US-2 explicitly excluded SPACs. US-3 does not change that policy. De-SPAC creates corporate-action/successor risk and must not trigger automatic migration into a new Security. A post-de-SPAC operating company can only be considered through fresh current population + exact identity evidence in a later authorized stage.

## 15. Primary listing policy

Every later potential ADMIT must have:

- current Primary Listing;
- Primary MIC in `{XNYS, XNAS}`;
- current Primary Ticker;
- current Security Name and Share Class.

Historical membership/listing is insufficient.

Fail closed to REVIEW/EXCLUDE for delisted, obsolete, completed merger/acquisition, retired ticker, unresolved successor, unresolved exchange migration or ambiguous primary listing.

## 16. Security identity policy

Exact canonical identity for later ADMIT:

`Exact ISIN + Primary MIC + Primary Ticker + Exact Security Name + Exact Share Class`

CUSIP, CIK, FIGI and vendor identifiers are supporting reconciliation evidence only. Provider symbols are mappings, not identity.

## 17. ISIN policy

For every later ADMIT:

- ISIN non-empty;
- syntactically valid;
- Luhn PASS;
- semantically belongs to the exact Security and Share Class;
- current enough for the current listing/corporate-action state;
- not merely issuer-level;
- not copied from another share class;
- not silently constructed from CUSIP.

`CUSIP != ISIN`. CUSIP may support evidence but cannot replace or silently generate semantic ISIN under this gate.

## 18. Share-class policy

Each Class A/B/C or other ordinary class is independently identified. Same issuer does not imply same Security. If population evidence and identity evidence disagree on class, status is REVIEW/CONFLICT until resolved. No silent class merge.

## 19. Corporate-action policy

Merger, acquisition, spin-off, split, reverse split, ticker change, exchange change, reincorporation, share-class conversion, name change, de-SPAC, delisting and successor events are fail-closed identity events.

If current identity is not unequivocal => REVIEW. Completed retired Securities => EXCLUDE. No automatic successor mapping or inherited membership. Any successor requires its own current Security-level evidence.

## 20. US-1 / US-2 overlap policy

A later US-3 build must check at least:

A. exact canonical identity: ISIN + Primary_MIC + Primary_Ticker  
B. ISIN overlap  
C. ticker overlap  
D. issuer/name similarity  
E. share-class overlap  
F. corporate-action/successor overlap

Outcomes:

- full canonical identity already present => `ALREADY_PRESENT`, no duplicate write;
- same ISIN with changed/different MIC or ticker => `CONFLICT / REVIEW`, no silent merge;
- same ticker with different ISIN => investigate; ticker is not identity;
- same issuer with different class => separate Security possible only with full class-specific evidence.

US-1 372 and US-2 369 are closed integrated populations and are not reopened by US-3.

## 21. Index-migration policy

S&P 500/400/600 membership is population evidence, not persistent identity. A Security may migrate between index segments.

If a current S&P SmallCap 600 member is already present in Research Partial from US-1/US-2 or another legacy path, classify `ALREADY_PRESENT`; update/write is not authorized here. Provenance/membership handling is separate and must not produce a duplicate Security row.

## 22. Full Research-Partial collision policy

A later US-3 Admission Build must collision-check against the complete **2527-row Research Partial**, not only US-1/US-2.

Minimum collision rules:

- duplicate WS_ID => FAIL;
- duplicate full canonical identity => ALREADY_PRESENT / no duplicate write;
- non-empty duplicate ISIN with divergent canonical tuple => CONFLICT / REVIEW;
- ticker-only collision => not automatically an error;
- same ticker across different markets => allowed only when canonical identity is distinct;
- same issuer / different class => separate Security only with exact evidence;
- successor/corporate-action ambiguity => REVIEW.

## 23. Admission states

A later build must support at least:

- `ADMIT` — all hard requirements pass; eligible for later evidence/write gating, not automatically written.
- `REVIEW` — potentially admissible but one or more resolvable identity/instrument/corporate-action questions remain.
- `EXCLUDE` — policy-prohibited instrument or retired/non-target Security.
- `ALREADY_PRESENT` — canonical Security already exists; no duplicate row.
- `CONFLICT` — incompatible identity/evidence values require resolution.
- `INVALID` — malformed/invalid identifier or impossible Security tuple.
- `BLOCKED` — required evidence layer not reproducibly available.

## 24. ADMIT requirements

ADMIT is possible only if all are true:

- current S&P SmallCap 600 membership verified under the population hard gate;
- current primary listing verified;
- Primary MIC = XNYS or XNAS;
- exact current Primary Ticker;
- exact Security Name;
- exact Share Class;
- allowed Common/Ordinary instrument type;
- exact semantic ISIN;
- ISIN syntax + Luhn PASS;
- corporate-action state clear;
- no unresolved identity conflict;
- not a prohibited instrument;
- full Research-Partial canonical collision QA passed.

## 25. REVIEW conditions

REVIEW at minimum for unresolved share class, REIT/BDC/LP/MLP, preferred/pref-only path, unresolved corporate action, conflicting identifier, ambiguous primary listing, same ISIN with divergent canonical tuple, foreign-incorporated ambiguity, unresolved successor or unclear instrument type.

## 26. EXCLUDE conditions

EXCLUDE at minimum for ADR/ADS/DR, ETF, Fund, Unit, Warrant, Right, Structured Product, SPAC (common/unit/warrant), foreign secondary listing, obsolete/delisted Security, completed acquisition with retired Security and any other explicitly prohibited instrument class.

## 27. Evidence provenance requirements

Every later evidence layer must record:

- Source;
- Source Rank;
- Snapshot Date / As-of-Date;
- Retrieval Date;
- Population;
- Evidence Type;
- Security-level identifiers available;
- provenance/materialization path;
- completeness/coverage where relevant.

No unprovenanced candidate rows.

## 28. Canada/Korea failure-mode control

US-3 must not proceed merely because US data has historically been easier. The next stage must prove the population evidence before candidate admission. If current population evidence cannot be reproduced, US-3 fails closed before build rather than entering a manual identity-recovery loop.

Capability assessment based on existing repository architecture:

| Capability | Assessment | Basis |
|---|---|---|
| Population Evidence Capability | CONDITIONAL | bounded S&P 600 concept exists; current reproducible snapshot not yet proven in this gate |
| Listing Evidence Capability | STRONG | US-1/US-2 XNYS/XNAS listing architecture is established |
| Security Identity Capability | STRONG | 741 US rows integrated with zero post-audit identity duplicates |
| ISIN Capability | STRONG | exact ISIN controls established; 741 integrated US rows had complete identity |
| Instrument Classification Capability | STRONG | US-1/US-2 instrument matrix and fail-closed handling established |
| Corporate Action Capability | CONDITIONAL | policy can fail closed, but small-cap turnover/migration must be proven Security-by-Security in later build |
| Scalability | YES | US evidence/identity pipeline has already scaled across S&P 500 and 400 paths |

**Canada/Korea Failure-Mode Risk: LOW / MEDIUM.** The residual risk is concentrated in population-snapshot reproducibility and small-cap corporate-action turnover, not the core US identity tuple.

## 29. US-1/US-2 architecture transferability

**US-1/US-2 Architecture Transferability: CONDITIONAL.**

The listing, identity, ISIN, instrument, overlap and collision architecture transfers without a new semantic assumption. The one central condition is:

> A current, reproducible, Security-level S&P SmallCap 600 population snapshot with explicit As-of-Date, provenance and measurable completeness must be materialized and validated before any Candidate Admission Build.

No assumption is made in this Policy Gate that such a source is currently available.

## 30. Build readiness

**BUILD READINESS: READY WITH CONDITIONS.**

Policy architecture is complete and the US identity path is proven. The remaining central gap is narrowly bounded: Population Evidence remains CONDITIONAL and must pass the hard gate before build. This is not a reason to reopen broad feasibility or to start a build prematurely.

## 31. Exact next authorized stage

**NEXT AUTHORIZED STAGE: US-3 Population Evidence Validation Gate — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

That stage may validate/materialize the already policy-defined population evidence only under its own explicit authorization. It must prove reproducibility, As-of-Date, Security-level coverage and provenance before any Admission Build can be authorized.

This Policy Gate does **not** authorize `US-3 Admission Build` directly.

## 32. No-touch confirmation

No S&P SmallCap 600 constituents were downloaded. No new source hunt was started. No population snapshot, candidate file, holdings file or evidence sidecar was created. No Admission or Build was performed. Research Partial remains 2527; Strict 759; Frozen 0; US-1 372; US-2 369; AU-1 153. Canada and Korea remain PARKED. No Universe, Membership, Mapping, History, Liquidity, Eligibility, Scan/U3K or Welt-Swing-v7.2 artifact was changed.

## 33. Quality gates G0-G17

- G0 Correct origin/main HEAD — PASS
- G1 Correct authorized US-3 Policy stage — PASS
- G2 Research Partial 2527 verified — PASS
- G3 Strict 759 verified — PASS
- G4 Frozen 0 verified — PASS
- G5 US-1 372 / US-2 369 verified — PASS
- G6 S&P SmallCap 600 boundary defined — PASS
- G7 Population Evidence policy defined — PASS
- G8 Instrument policy defined — PASS
- G9 Security Identity / ISIN policy defined — PASS
- G10 Share-Class / Corporate-Action policy defined — PASS
- G11 US-1/US-2 overlap and index-migration controls defined — PASS
- G12 Full Research-Partial collision controls defined — PASS
- G13 Canada/Korea failure-mode controls applied — PASS
- G14 Build Readiness exactly classified — PASS (`READY WITH CONDITIONS`)
- G15 Exact next READ-ONLY/SIDECAR stage defined — PASS
- G16 No Universe/Data write — PASS
- G17 No follow-on stage executed — PASS

**US-3 ADMISSION POLICY GATE — PASS**

**BUILD READINESS: READY WITH CONDITIONS**

**NEXT AUTHORIZED STAGE: US-3 Population Evidence Validation Gate — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**
