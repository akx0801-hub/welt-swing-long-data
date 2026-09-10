# FTSE TWSE Taiwan 50 Admission Policy Gate

## Stage decision

**FTSE TWSE TAIWAN 50 ADMISSION POLICY GATE — PASS**

**BUILD READINESS: READY WITH CONDITIONS**

**NEXT AUTHORIZED STAGE: FTSE TWSE Taiwan 50 Population/Identity Currentness Validation Gate — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

This is a policy-only stage. It performs no source hunt, no FTSE/TWSE refresh, no population rematerialization, no ISIN recovery, no individual-security research, no candidate generation, no admission/build, no Research-Partial/Membership/Universe/Frozen write, and no mapping/history/liquidity/eligibility/scan or productive Welt-Swing v7.2 work.

## 1. Start HEAD and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `9d6ade6ff6c10003597146e211a13fd3f4b72b2a`
- origin/main at startcheck: `9d6ade6ff6c10003597146e211a13fd3f4b72b2a`
- Verified predecessor commit: `Post-Brazil next population manager gate`
- Authorized stage: **FTSE TWSE Taiwan 50 Admission Policy Gate — READ-ONLY**

Central repository artifacts actually used:

- `docs/spec/Post_Brazil_Next_Population_Manager_Gate.md`
- `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`
- `docs/spec/P5_0_Architecture_Coverage_Gate.md`
- `output_current_master_reconciliation_v0_28/current_master_identity_quality_v0.28.csv`
- `output_current_master_reconciliation_v0_28/current_master_source_authority_audit_v0.28.csv`
- `output_current_master_missing_source_materialization_v0_29/imported_segment_provenance_carryforward_v0.29.csv`
- `docs/validation/P4_Composition_Coverage_Audit_759.md`
- relevant prior US-1/US-2/AU-1/Canada/Korea/US-3/Brazil governance artifacts already incorporated by the predecessor manager gate.

No new source, provider, endpoint, constituent list, Security Master or security-level web lookup was used.

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
| Brazil | PARKED |
| Taiwan target | FTSE TWSE Taiwan 50 |
| Primary market | Taiwan Stock Exchange |
| Primary MIC | XTAI |
| Existing source lineage | SRC_FTSE_TW50_CW_20260630 |
| Existing population rows | 50 |
| Existing strict ISIN+MIC+ticker identity | 47/50 |
| Missing ISIN | 3/50 |
| Historical Strict coverage | 49/50 |
| Population source As-of | 2026-06-30 |

The repository therefore confirms the manager baseline. Research Partial 2527 remains a workbench/research state; Strict 759 is not Membership; Frozen remains 0.

## 3. Exact population boundary

The sole authorized population boundary is:

**the exact 50-security `TW_TW50 / FTSE TWSE Taiwan 50` population already represented by repository lineage `SRC_FTSE_TW50_CW_20260630`.**

Excluded from this boundary are broader Taiwan equities, TPEx/OTC populations, free-form Taiwan lists, ADRs, GDRs, foreign secondary listings, MSCI Taiwan, general TAIEX populations and any security outside the existing 50-row lineage.

**Population Boundary Clarity: HIGH.**

No population rematerialization or constituent update is authorized here.

## 4. Existing source-lineage assessment

Repository audit evidence records:

- Segment: `TW_TW50`
- Target index: FTSE TWSE Taiwan 50
- Source lineage: `SRC_FTSE_TW50_CW_20260630`
- Rows: 50
- Source-AsOf populated rows: 50
- Last-validated populated rows: 50
- Source As-of range: 2026-06-30
- Strict `ISIN + Primary_MIC + Primary_Ticker` rows: 47
- Fallback `MIC + ticker + WS_ID` rows: 3
- Missing ISIN rows: 3
- Missing Primary MIC rows: 0
- Missing Primary Ticker rows: 0

However, the source-authority audit also labels the lineage `CURRENT_MASTER_LINEAGE_IMPORTED_BUT_SOURCE_EVIDENCE_AUDIT_REQUIRED`, with source-gate state `IMPORTED_PENDING_EXPLICIT_SOURCE_EVIDENCE_FREEZE_AUDIT`; the v0.29 carryforward retains `CURRENT_MASTER_IMPORTED_PROVENANCE_FREEZE_STILL_REQUIRED`.

Policy assessment:

- Population Authority: **CONDITIONAL**
- Population Completeness: **STRONG**
- Security Identity Capability: **STRONG**
- ISIN Capability: **STRONG** for the overwhelming majority, with 3 isolated gaps
- Primary Listing Capability: **STRONG**
- Share-Class Capability: **STRONG** at architecture/policy level
- Currentness: **CONDITIONAL**

The source lineage is therefore strong enough to define admission rules, but currentness/provenance must be validated before a build can rely on it as current admission evidence.

## 5. Population currentness policy

Population As-of-Date is **2026-06-30**. Current stage date is 2026-09-10.

The existing 50-row lineage must not be silently treated as current admission evidence. Before any Admission Build, one bounded validation must confirm that the locked source lineage remains sufficiently current for the admission decision and that any membership changes since 2026-06-30 are identified without broadening the population.

**Population Currentness: CONDITIONAL.**

Policy requirement:

- Population membership evidence used for admission must be demonstrably current enough relative to build date.
- Any constituent replacement, deletion or addition is not silently applied to the locked lineage; it must be explicitly reconciled under the later currentness gate.
- If currentness cannot be validated reproducibly, no Admission Build is authorized.

## 6. Canonical Taiwan security identity

Canonical identity is:

`ISIN + Primary_MIC + Primary_Ticker / Local Security Code + Exact Security Name + Exact Share Class`

For Taiwan:

- exact security-level ISIN;
- Primary MIC `XTAI`;
- exact local TWSE security code as Primary Ticker;
- exact security name under repository/source conventions;
- exact share class.

Issuer identity is not security identity. No issuer-only, fuzzy-name, ADR/GDR or alternate-market substitution is permitted.

**Canonical Identity Architecture: STRONG.**

## 7. Primary XTAI listing policy

Later admission requires the concrete local security to have Primary Market = Taiwan Stock Exchange and Primary MIC = `XTAI`.

Not acceptable as substitutes:

- ADR;
- GDR;
- foreign secondary listing;
- OTC representation;
- TPEx listing where the population row is an XTAI constituent;
- depositary receipt.

Existing Taiwan workbench rows already carry XTAI and no Primary MIC gap is recorded, so the architecture is strong; later row-level currentness still must be checked.

**Primary Listing Architecture: STRONG.**

## 8. Local security-code policy

The exact TWSE local security code is the central primary-market join key.

Rules:

- exact code required;
- preserve code formatting, including any leading zeros if present;
- exchange/vendor suffixes are mappings, not part of canonical local code identity unless a repository field explicitly stores them separately;
- no aggressive ticker normalization;
- no fuzzy ticker mapping;
- no automatic ADR/local mapping;
- MIC + code divergence is a hard conflict pending resolution.

**Local Security-Code Architecture: STRONG.**

## 9. Security-name and script policy

The canonical security name is the exact name carried by the authoritative source/evidence selected under existing governance. Local-language and English names may coexist as aliases/cross-checks but may not independently create identity.

Permitted normalization:

- conservative Unicode normalization;
- whitespace normalization;
- documented punctuation normalization;
- existing repo-approved aliases.

Not permitted:

- aggressive fuzzy merging;
- automatic translation as identity proof;
- issuer-only matching;
- collapsing multiple securities/classes because names are similar.

Where name variants conflict, `XTAI + local code + exact ISIN + share class` outrank spelling variants, but unresolved substantive name conflicts fail closed.

## 10. Instrument policy

The global DEV U3K instrument architecture remains authoritative and is applied with Taiwan-specific market identity, not copied mechanically from US examples.

| Instrument category | Policy outcome |
|---|---|
| Ordinary/Common Equity | POTENTIALLY ADMIT |
| Preferred Equity | EXCLUDE |
| ETF | EXCLUDE |
| Fund | EXCLUDE |
| ADR | EXCLUDE |
| GDR | EXCLUDE |
| Depositary Receipt | EXCLUDE |
| Rights | EXCLUDE |
| Warrants | EXCLUDE |
| Structured Product | EXCLUDE |
| Debt | EXCLUDE |
| Foreign Secondary Listing | EXCLUDE |
| Unknown Instrument | REVIEW |

Only ordinary/common local primary equities may proceed to all remaining admission hard gates.

## 11. Share-class policy

**Exact Share Class Required: YES.**

Rules:

- Ordinary != Preferred.
- Different valid share classes are distinct securities.
- Same issuer does not imply same security.
- Same company with another local code is not automatically identical.
- ISIN must belong to the exact class.
- No class substitution from ADR/GDR or another market.

**Share-Class Architecture: STRONG.**

The DEV rule allowing one canonical scan class where multiple eligible ordinary classes exist remains a later scan-universe selection rule; it does not permit silent identity merging at admission.

## 12. Same issuer / multiple securities

The same issuer may have multiple canonical securities if exact security identities differ by ISIN, local security code and/or share class. Deduplication is security-level, never issuer-level.

## 13. Depositary-receipt policy

A local XTAI security and an ADR/GDR of the same issuer are different securities. An ADR/GDR in Research Partial is not an automatic collision with the local Taiwan share.

**ADR/GDR Accepted as Local Substitute: NO.**

## 14. ISIN hard gate

A later Taiwan admission requires exact security-level ISIN evidence.

Required:

- non-empty;
- exactly 12 characters;
- syntax valid;
- Luhn PASS;
- exact security-level match;
- exact share-class match;
- consistent with XTAI/local security code/current security identity.

Forbidden:

- synthetic ISIN;
- ISIN derived from ticker or issuer identifier;
- issuer-level ISIN;
- another share-class ISIN;
- ADR/GDR ISIN substituted for local share;
- workbench ISIN accepted solely because it already exists in Research Partial.

**Exact Security-Level ISIN Required: YES.**

## 15. Policy for the three ISIN-gap rows

Repository evidence establishes 47/50 strict identity rows and three rows with missing ISIN while Primary MIC and ticker remain present.

**ISIN Gap Type: ISOLATED.**

The gap is not population-wide and is not evidence of a systemic Taiwan identity failure. Therefore the three gap rows do not block policy definition for the other 47.

Later build rule:

- a row with no exact authoritative ISIN cannot be ADMIT;
- such a row must fail closed to a non-admitted/review outcome;
- no ISIN recovery loop is required merely to allow the other validated rows to proceed;
- no synthetic or inferred ISIN is permitted.

**Can ISIN-Gap Rows Fail Closed in Build: YES.**

The three gaps alone do not require a separate recovery gate.

## 16. Security-identity currentness policy

Existing 47/50 ISIN identities may be reused later only if their evidence is still date-compatible with the admission date and remains attached to the same concrete XTAI security and share class.

**Identity Currentness Requirement:** before admission, confirm that each reused canonical tuple remains consistent with the current XTAI local code, security name/share class and any known corporate-action state; stale or changed identifiers fail closed and are not automatically carried forward.

This currentness validation must be bounded and population-wide, not security-by-security recovery.

## 17. Corporate-action policy

Fail-closed review is mandatory for:

- local-code/ticker change;
- company rename where identity continuity is not explicit;
- merger;
- spin-off;
- share conversion;
- share-class conversion;
- delisting/relisting;
- successor security;
- ISIN change.

No automatic successor mapping is permitted. If population evidence and identity evidence are temporally inconsistent, admission is blocked for the affected row until the bounded currentness validation establishes the current tuple.

**Corporate-Action Policy: DEFINED.**

## 18. Evidence hierarchy

For later admission:

- **R1:** official exchange, index administrator, regulatory or market-infrastructure evidence;
- **R2:** official issuer evidence only where security-level identity is explicit;
- **R3:** already repository-qualified institutional security-level evidence;
- **R4:** only where existing governance has explicitly qualified the exact source/evidence class.

Secondary finance sites, brokers, community sites and generic web sources are not final authority. This policy gate qualifies no new source.

## 19. Full Research-Partial collision policy

Every later candidate row must be checked against all **2527 Research Partial rows**.

Collision keys:

1. exact ISIN;
2. exact `Primary_MIC + Primary_Ticker`;
3. exact conservatively normalized Security Name + exact Share Class;
4. issuer similarity: diagnostic only;
5. corporate-action relation: diagnostic only.

Required outcomes:

- `NO_EXISTING_COLLISION`
- `ALREADY_PRESENT`
- `POTENTIAL_IDENTITY_CONFLICT`
- `ISIN_CONFLICT`
- `MIC_TICKER_CONFLICT`
- `SHARE_CLASS_CONFLICT`
- `CORPORATE_ACTION_REVIEW`
- `UNRESOLVED`

Exact same ISIN with a fully consistent tuple is `ALREADY_PRESENT`, never a duplicate write. Same ISIN with divergent MIC/ticker/name/class is `POTENTIAL_IDENTITY_CONFLICT`. Same XTAI+local code with different ISIN is a hard `MIC_TICKER_CONFLICT` until resolved. Name similarity alone is never a hard collision.

## 20. 47/50 vs 49/50 policy reconciliation

The two counts describe different layers and are not intrinsically contradictory:

- **47/50** = strict identity-quality rows with complete non-empty `ISIN + Primary_MIC + Primary_Ticker` in the v0.28 identity audit;
- **49/50** = historical Strict coverage in an eligibility/coverage stage.

A later build must distinguish at least:

- historical Strict row with complete current canonical identity;
- historical Strict row lacking current authoritative ISIN evidence;
- Research-Partial-only row;
- population row absent from Research Partial;
- conflicting identity row.

Historical Strict status does not itself prove membership or admission and cannot waive any identity/currentness/collision hard gate.

## 21. Fail-closed build rules

A future build may process clean rows while isolating row-specific gaps only if:

- population boundary is stable;
- currentness is validated;
- XTAI/local-code identity is stable;
- gaps are isolated;
- no systemic source/identity contamination exists;
- no uncontrolled manual recovery is required.

Minimum row-level admission hard gates:

- Population Membership PASS;
- Primary Listing PASS;
- Primary MIC XTAI;
- exact Local Security Code PASS;
- Security Name PASS;
- Instrument Policy PASS;
- Share Class PASS;
- ISIN present;
- ISIN syntax PASS;
- ISIN Luhn PASS;
- Security-Level Match PASS;
- Share-Class Match PASS;
- Currentness PASS;
- Research-Partial Collision CLEAR;
- Corporate Action CLEAR.

Only then may a later build produce `ADMIT`.

## 22. Failure-mode assessment

Taiwan differs materially from the parked markets:

- Canada: broad security-level identity recovery failed repeatedly; Taiwan already has 47/50 strict canonical identity tuples.
- Korea: population/listing/identity access was structurally non-reproducible; Taiwan already has a complete 50-row lineage and stable XTAI architecture.
- US-3: strong theory failed on raw materialization; Taiwan does not require a new source architecture for policy, but existing source currentness still needs a bounded validation before build.
- Brazil: 79/79 eligible rows had a systemic ISIN gap and the sole batch path failed materialization; Taiwan has only three isolated ISIN gaps.

Risk ratings:

- Canada Failure-Mode Risk: LOW
- Korea Failure-Mode Risk: LOW
- US-3 Failure-Mode Risk: MEDIUM
- Brazil Failure-Mode Risk: LOW

The remaining risk is currentness/provenance, not a broad identity recovery problem.

## 23. Manual-recovery assessment

**Expected Security-by-Security Manual Recovery: LOW.**

The policy does not require recovery of the three ISIN gaps. They may fail closed later. The one required pre-build condition is population/identity currentness validation for the 50-row lineage as a whole.

**Generic Source Hunt Required: NO.**

## 24. Build readiness

**BUILD READINESS: READY WITH CONDITIONS.**

The admission architecture itself is sufficiently defined and strong:

- population boundary HIGH;
- exact 50-row lineage exists;
- XTAI primary-listing architecture strong;
- local-code architecture strong;
- canonical identity architecture strong;
- ISIN architecture strong for 47/50 with only three isolated fail-closed gaps;
- share-class architecture strong;
- collision policy complete;
- no generic source hunt or broad manual recovery required.

The single remaining precondition is **currentness**. The source lineage is dated 2026-06-30 and repository source-audit state explicitly says provenance/source evidence still required freeze/audit. On 2026-09-10 this is too old to treat silently as current admission evidence.

**Blocking Condition:** current population membership and reused identity/listing tuples must be validated as date-compatible with an Admission Build; this must be resolved in one bounded currentness gate before build.

The three missing-ISIN rows are not the blocking condition and need no separate recovery gate.

## 25. Exact next authorized stage

**FTSE TWSE Taiwan 50 Population/Identity Currentness Validation Gate — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

Purpose of that single gate: validate the currentness/provenance of the existing 50-row `SRC_FTSE_TW50_CW_20260630` population and the date-compatibility of existing XTAI/local-code/security-identity tuples. It may fail-close stale/changed rows. It must not become a three-row ISIN recovery loop, generic source hunt or Admission Build.

If that bounded currentness gate passes sufficiently for clean rows, the next stage may be an Admission Build. No such follow-on is executed here.

## 26. No-touch confirmation

No Research Partial, Membership, Universe, Strict, Frozen, US-1, US-2, US-3, AU-1, Canada, Korea, Brazil or Taiwan population state was changed. No population was rematerialized. No source/evidence/candidate/admission sidecar was created. No mapping/history/liquidity/eligibility/scan/U3K or productive v7.2 work was performed.

## 27. Quality gates G0-G17

- G0 Correct origin/main HEAD — PASS
- G1 Correct FTSE TWSE Taiwan 50 Admission Policy stage — PASS
- G2 Research Partial 2527 verified — PASS
- G3 Strict 759 verified — PASS
- G4 Frozen 0 verified — PASS
- G5 Canada/Korea/US-3/Brazil remain PARKED — PASS
- G6 Existing 50-row Taiwan population recognized without rematerialization — PASS
- G7 SRC_FTSE_TW50_CW_20260630 lineage assessed — PASS
- G8 XTAI primary-market policy defined — PASS
- G9 Canonical identity policy defined — PASS
- G10 Instrument/share-class policy defined — PASS
- G11 ISIN hard gate retained — PASS
- G12 Three ISIN-gap policy explicitly defined — PASS
- G13 Full 2527-row Research-Partial collision policy defined — PASS
- G14 Currentness/corporate-action policy defined — PASS
- G15 Build Readiness exactly READY WITH CONDITIONS — PASS
- G16 No universe/membership/research-partial write — PASS
- G17 No follow-on stage executed — PASS

**G0-G17: PASS**

## 28. Final state

**FTSE TWSE TAIWAN 50 ADMISSION POLICY GATE — PASS**

**BUILD READINESS: READY WITH CONDITIONS**

**NEXT AUTHORIZED STAGE: FTSE TWSE Taiwan 50 Population/Identity Currentness Validation Gate — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

HARD STOP.