# Canada Rebuild Admission Policy Gate

## Decision

**CANADA REBUILD ADMISSION POLICY GATE — PASS**

**READY FOR SEPARATE CANADA REBUILD ADMISSION BUILD**

“Ready” here means that the policy is defined sufficiently for a separately authorized later Build stage. This document itself performs no Build, Admission, candidate generation, Mapping or Universe write.

## Start and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `6a858873279281d76d8bd2cf4c6ca3b331e67700`
- Starting commit: `Canada targeted recovery manager gate`
- Authorized stage: Canada Rebuild Admission Policy Gate — READ-ONLY
- Research Partial: 2527
- Strict: 759
- Frozen: 0

## Legacy Canada state

- Legacy Canada Membership: 217
- Legacy exact-ready: 0
- Canada v2: 0/217 EVIDENCE_READY
- Targeted recovery: 0/30 RECOVERY_READY
- Legacy Canada handling: unchanged

The failed legacy recovery does not prove that the 217 rows are false. It proves that they are not a sufficient reproducible Security-level identity source for a new admission pipeline. The 217 rows remain historical Research/Membership context and are not silently deleted, replaced or migrated.

## Rebuild principle

The rebuild is a new Population/Admission pipeline, not Legacy-Recovery v3. Membership evidence, listing evidence and Security identity evidence are separate evidence layers. Admission occurs only when all required layers pass for the same concrete Security and Share Class.

The v0.1 architecture is respected: official Universe membership is preferred; unavailable official full sources must be documented as blocked rather than silently replaced by third-party lists. Strict identity remains fail-closed.

## Final population architecture

**Population Source: S&P/TSX Composite as the single primary Canada rebuild population.**

Rationale:

- broader Canada coverage than the S&P/TSX 60;
- more coherent and reproducible than an arbitrary ETF-holdings union;
- captures large and mid-cap Canadian sector breadth;
- avoids defining a new free-form Canada universe;
- aligns membership with an official index-family source.

The S&P/TSX 60 is treated as a subset/cross-check, not a second parallel population. S&P/TSX Completion is not independently unioned into the first rebuild unless the later Policy/Build implementation documents that it is the official non-overlapping Composite decomposition and proves reconciliation. The first build must not create duplicate or ambiguous membership through parallel index sources.

If the official Composite constituent source is not technically reproducible at Build time, the later Build must stop or document the segment as blocked. It may use an institutionally maintained Composite proxy only as a documented fallback, with official TMX/TSX listing verification and explicit coverage disclosure. An ETF holdings file is not a substitute for official Composite membership.

## Evidence policy

### Membership evidence

Required: evidence that the exact Security belongs to the selected S&P/TSX Composite population.

Preferred order:

1. R1 official S&P Dow Jones Indices constituent source or official index administrator output;
2. an institutionally maintained Composite proxy only when the official full constituent source is inaccessible, with the blocked-source limitation recorded;
3. no anonymous list, Wikipedia, generic screener, issuer list or ETF holdings file as sole membership proof.

### Listing evidence

Required from official TMX/TSX or equivalent official exchange context:

- current listing status;
- exchange;
- Primary_MIC;
- Primary_Ticker;
- exact listed Security/Class.

The existing v0.1 rule that a Security identity is independent of provider symbols is retained. Yahoo or other provider symbols are mappings, not identity.

### Security identity evidence

Required for the same Security/Class:

- exact issuer;
- exact Security name;
- exact Share Class;
- Instrument Type;
- ISIN;
- Primary Exchange;
- Primary MIC;
- Primary Ticker.

Issuer IR, annual reports, prospectuses and SEDAR+ filings may provide Class and instrument evidence. An official or institutional identifier source may provide ISIN. R3 material is supporting only. R4 is discovery only.

### Source hierarchy

- **R1 — Official primary:** S&P Dow Jones/index administrator; TMX/TSX; issuer IR and official security documents; SEDAR+ and official filings; official corporate-action notices.
- **R2 — Institutional:** iShares, Vanguard, BMO, RBC, other institutional index/ETF holdings and established identifier data.
- **R3 — Strong secondary:** supporting cross-check only.
- **R4 — Discovery only:** search engines and generic finance pages.
- **Alpha Vantage:** prohibited.

## Exchange and MIC scope

**Primary exchange scope: Toronto Stock Exchange primary listings, MIC XTSE.**

**TSX Venture: OUT OF SCOPE for the first rebuild.**

`XTSX` securities must not be silently merged into the XTSE population. Other Canadian MICs are out of scope unless a later Policy Gate explicitly expands the policy. A Canadian issuer with only a foreign primary and a Canadian secondary listing is not eligible under this first rebuild.

## Instrument policy

| Instrument class | Policy |
|---|---|
| Common / Ordinary | ADMITTABLE if all hard gates pass |
| Preferred | REVIEW |
| REIT | REVIEW |
| Trust | REVIEW |
| Unit | REVIEW |
| ETF / Fund | EXCLUDE |
| Depositary Receipt | EXCLUDE |
| Foreign Secondary Listing | EXCLUDE |
| Structured Product | EXCLUDE |
| Warrant | EXCLUDE |
| Right | EXCLUDE |
| Other / unresolved | REVIEW |

REVIEW is not Admission. REIT, Trust and Unit cases need later instrument-specific governance and eligibility treatment. The policy follows the v0.1 standard that Common/Ordinary shares are the default pass class, while non-standard instruments are not silently admitted.

## Multiple-class policy

Each listed Share Class is a separate Security. Class A, Class B, Voting, Non-Voting, Subordinate Voting, Multiple Voting, Variable Voting and Restricted Voting classes require their own:

- ISIN;
- Primary Ticker;
- Primary MIC;
- Security/Class evidence.

No issuer-level aggregation is allowed. A class may be admitted only when the evidence identifies the exact class represented by the listing and ISIN. Missing or conflicting class evidence is REVIEW.

## ISIN policy

ADMIT requires an ISIN from a reproducible R1/R2 or qualifying R3 source. The pipeline must:

1. validate format;
2. validate the check digit/Luhn;
3. match the ISIN to the exact Security;
4. match the ISIN to the exact Share Class;
5. match the ISIN to the verified Primary MIC and Ticker.

CUSIP is a cross-check or research anchor only. It cannot replace ISIN or establish identity alone. No Canadian prefix may be assumed and no ISIN may be constructed.

## Current listing and corporate-action policy

Only current `ACTIVE` primary listings are admissible.

- `ACTIVE`: eligible for hard-gate evaluation.
- `DELISTED`, `MERGED`, `ACQUIRED`, `SUCCESSOR`, `SUSPENDED`: REVIEW or EXCLUDE according to documented current-security evidence; never silently map to a successor.
- `UNKNOWN`: REVIEW.

Corporate-action states requiring Security-level revalidation include RENAME, TICKER_CHANGE, CLASS_CHANGE, MERGER, ACQUISITION, DELISTING, SUCCESSOR_SECURITY and OTHER/UNRESOLVED. A historical issuer match is not a substitute for current Security identity.

## Canonical identity

The canonical identity is:

**ISIN + Primary_MIC + Primary_Ticker + exact Share Class**

The canonical `WS_ID` follows the existing repository format based on the verified primary listing, e.g. `WS:XTSE:<ticker>`. Provider symbols remain separate mapping fields. No ticker-only cross-MIC identity is permitted.

## Collision and legacy-overlap policy

Against the current Research Partial 2527, the later Build must classify:

- `EXACT_IDENTITY_DUPLICATE`;
- `ISIN_DUPLICATE`;
- `MIC_TICKER_DUPLICATE`;
- `TICKER_ONLY_CROSS_MIC`;
- `TRUE_IDENTITY_CONFLICT`.

Rules:

- exact duplicate: not a new admission;
- true identity conflict: REVIEW and fail closed;
- ticker-only cross-MIC: document, but do not treat as an identity conflict by itself;
- no automatic merge.

Against the 217 legacy Canada rows, measure exact identity, ticker and issuer overlap separately. Results must be classified as NEW, ALREADY_PRESENT_EXACT, LEGACY_MATCH_REVIEW or CONFLICT. The legacy rows are not a truth source and are not automatically replaced.

## Admission model

Every candidate receives exactly one final status:

- `ADMIT`;
- `REVIEW`;
- `EXCLUDE`.

An optional internal `INSTRUMENT_REVIEW` reason may be recorded under REVIEW; it is not a fourth admission outcome.

### ADMIT hard gates

All must pass:

- verified S&P/TSX Composite membership;
- current ACTIVE listing;
- XTSE primary listing;
- admissible Common/Ordinary instrument;
- exact Security and Share Class;
- valid and semantically matching ISIN;
- verified Primary_MIC and Primary_Ticker;
- no unresolved corporate action;
- no TRUE_IDENTITY_CONFLICT;
- no prohibited instrument class.

### REVIEW

Use REVIEW when ISIN, Share Class, Instrument Type, current listing, Primary Listing, Corporate Action, Multiple-Class identity, legacy overlap or collision evidence is incomplete or conflicting, and for Preferred/REIT/Trust/Unit pending later governance.

### EXCLUDE

Use EXCLUDE only when evidence establishes:

- ETF, Fund, Depositary Receipt, Foreign Secondary Listing, Structured Product, Warrant or Right;
- delisted/obsolete security with no eligible current Security;
- exact duplicate already present and not a new admission;
- another clearly prohibited class.

Missing evidence alone is REVIEW, not EXCLUDE.

## Expected coverage and size

No artificial target count is set. The resulting size follows the official S&P/TSX Composite membership and the hard gates. Quality, current listing status, reproducibility and identity safety take priority over maximizing rows. The later Build must report official-source coverage, blocked segments, admitted count, review count, excluded count and collision results.

## Build-readiness decision

The policy is complete enough for a separate implementation stage.

**READY FOR SEPARATE CANADA REBUILD ADMISSION BUILD**

This does not authorize that Build. The Build requires its own explicit stage authorization and must generate separate candidate/admission artifacts. No candidates, constituents, sidecars or Universe rows are created here.

## Quality gates

- G0 Correct `origin/main` HEAD: PASS
- G1 Correct authorized stage: PASS
- G2 Legacy Canada 217 unchanged: PASS
- G3 Rebuild treated as new pipeline: PASS
- G4 Population architecture defined: PASS
- G5 Source hierarchy defined: PASS
- G6 Membership vs identity evidence separated: PASS
- G7 Primary exchange scope defined: PASS
- G8 TSX Venture policy defined: PASS
- G9 Instrument policy defined: PASS
- G10 Multiple-class policy defined: PASS
- G11 ISIN hard gate defined: PASS
- G12 Corporate-action policy defined: PASS
- G13 Collision policy defined: PASS
- G14 Legacy overlap policy defined: PASS
- G15 Admission/Review/Exclude rules defined: PASS
- G16 No Build/Admission/Universe write: PASS
- G17 Exact next stage decision defined: PASS

