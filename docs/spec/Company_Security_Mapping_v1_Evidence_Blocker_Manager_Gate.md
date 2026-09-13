# Company/Security Mapping v1 Evidence Blocker Manager Gate

## 1. Purpose

This report executes exactly the authorized stage:

**Company/Security Mapping v1 Evidence Blocker Manager Gate — READ-ONLY / MANAGER ONLY**

Purpose: classify the exact repository-evidence blocker behind the failed bounded implementation attempt and decide whether the already approved **Security-only + nullable Company_Key** v1 remains safely implementable from current repository evidence.

This stage performs no implementation, creates no mapping sidecar, modifies no Universe/source artifact, acquires no external evidence, performs no web/provider work, does not reopen P0 byte materialization, acquires no fundamentals, and does not run Guru ranking.

## 2. Start HEAD Verification

Repository: `akx0801-hub/welt-swing-long-data`  
Branch: `main`

Verified start state:

- HEAD: `82eac225c800d7ecf2362a24ad754be8d0338f63`
- latest commit: `Repair P0 normalization commit audit trail`
- no newer commit exists on `main` at manager inspection time
- Research Partial source path: `universe/research_partial_1633.csv`
- source blob SHA: `f8e0d521023d26f1da9e75b4b817b861f686bb41`
- historical filename retained; current file contains 2527 data rows
- source CSV modified by this stage: **NO**

Start Gate: **PASS**.

## 3. Fixed Baseline Preserved

The following state is treated as fixed and is not re-opened:

- Research Partial: **2527**
- Strict: **759**
- Frozen: **0**
- Universe expansion: **PAUSED — NOT ABANDONED**
- Productive authority: **Welt-Swing v7.2 only**
- WELT-SWING LONG DEV: **DEV / RESEARCH / SHADOW ONLY**
- duplicate non-empty ISIN: **0**
- rows missing ISIN: **1536**
- current row semantics: **one row = one security/listing**
- current Security Identity Contract: **PARTIAL**
- current Company Identity Contract: **MISSING**
- Primary Listing Model: **PARTIAL**
- Architecture Gap: **B — SECURITY IDENTITY ADEQUATE, COMPANY IDENTITY/MAPPING MISSING**

Approved v1 rules remain unchanged:

- every source row may receive a stable internal `Security_Key`;
- `WS_ID` is a **seed**, not the mutable identity authority;
- `ISIN`, `MIC` and ticker are identity attributes/cross-checks, not the internal key;
- `Company_Key` is nullable;
- Company_Key assignment requires independent repository evidence supporting issuer relation;
- name-only, ticker-only and fuzzy-name Company_Key assignment are forbidden;
- distinct listings and distinct share classes remain distinct;
- `Security_Key -> nullable Company_Key`, relationship `ISSUED_BY`;
- ISIN-missing rows default to `SECURITY_UNRESOLVED` / `UNRESOLVED` and must not become `IDENTITY_OK` merely because WS_ID, ticker, MIC or name exists.

## 4. Repository Evidence Relevant to the Blocker

### 4.1 Source artifact is materially readable

The current Research Partial CSV is materially accessible at the verified HEAD. Its header exposes the security/listing fields needed for a v1 security sidecar, including `WS_ID`, `Name`, `ISIN`, `Instrument_Type`, `Primary_Ticker`, `Primary_Exchange`, `Primary_MIC`, `Primary_Currency`, `Primary_Universe_Index`, `Share_Class` and source/provenance fields. The tail of the file is also readable and reaches the 2527-row current population.

Therefore the failed implementation is **not** explained by inability to materially access the canonical source artifact.

### 4.2 WS_ID is an established repository security seed

Repository history uses `WS_ID` as the stable row/security reference throughout mapping, history, liquidity, eligibility, audit and expansion work. Existing reports also preserve fallback identity patterns such as `Primary_MIC + Primary_Ticker + WS_ID` where ISIN is absent.

Therefore the implementation is **not** blocked because a security seed cannot be obtained.

### 4.3 Security identity is incomplete but explicitly fail-closed

The repository has a real security-evidence limitation: 1536 current rows lack ISIN and some historical segments rely on governed listing-level fallback identity rather than complete ISIN identity.

However the approved v1 contract already defines the required behavior for this limitation: create `Security_Key`, retain the partial identity attributes, and classify unresolved rows as `SECURITY_UNRESOLVED` / `UNRESOLVED` rather than promoting them to `IDENTITY_OK`.

Therefore incomplete ISIN coverage is a **quality/status condition**, not a blocker to creating the security sidecar.

### 4.4 Company identity/mapping evidence is the actual missing layer

The shared Fundamentals architecture explicitly separates Company Master from Security Master and states that unresolved identity/mappings remain explicit and fail-closed. Repository priority analysis further records that `Company_Key` and `Security_Key` are still largely target-architecture concepts and that a mature populated canonical company/security bridge is missing.

Current repository evidence is insufficient to assign `Company_Key` broadly without violating the approved prohibition on name-only, ticker-only or fuzzy issuer inference.

This is a genuine evidence gap.

### 4.5 The genuine company-evidence gap does not block v1

The approved v1 architecture intentionally permits `Company_Key = NULL` when issuer relation is not independently supported by repository evidence.

Consequently the absence of broad Company_Key evidence does **not** prevent a bounded security-first v1 from being generated safely. It only prevents unsupported company resolution.

## 5. A–G Blocker Classification

| Code | Candidate blocker | Manager result | Reason |
|---|---|---|---|
| A | Source artifact cannot be materially accessed/read | **NO** | Current 2527-row source CSV is materially readable, including schema and terminal rows. |
| B | WS_ID/security seed cannot be safely obtained | **NO** | WS_ID is present and is an established repository security reference/seed. |
| C | Required identity fields cannot be reliably obtained | **NO AS IMPLEMENTATION BLOCKER** | Complete identity is not available for all rows, especially 1536 missing-ISIN rows, but the approved contract explicitly permits unresolved status while still assigning Security_Key. |
| D | Company_Key evidence insufficient, but nullable Company_Key allows v1 | **YES — PRIMARY CLASSIFICATION** | Broad company/issuer mapping is not safely evidenced, while the approved v1 deliberately permits NULL Company_Key. |
| E | Generator/sidecar cannot be produced in current execution environment | **NO REPOSITORY-EVIDENCE BASIS** | No repository constraint requires external acquisition or mutable source data for a security-only sidecar. Ordinary deterministic CSV sidecar generation is already a normal repository pattern. |
| F | Previous implementation gate was over-constrained and no real blocker exists | **SECONDARY / PARTIAL** | The previous attempt was over-constrained only insofar as it treated the real Company_Key evidence gap as fatal to all v1 implementation. Because the company-evidence limitation is real, D is the more exact primary classification. |
| G | Other exact blocker | **NO** | No additional repository-evidence blocker is established. |

## 6. Manager Decision

**BLOCKER CLASSIFICATION: D — Company_Key evidence is insufficient, but nullable Company_Key allows v1.**

The prior failed attempt remains historically valid as a failed attempt: it produced no sidecar, no implementation files and no commit. This manager gate does not rewrite that history.

However its failure condition must **not** be carried forward as proof that the approved v1 architecture is unimplementable. The repository evidence supports a bounded security-first implementation provided unresolved company identity remains NULL and fail-closed.

## 7. Security-only + Nullable Company_Key v1 Assessment

**SAFE IMPLEMENTABILITY: YES — WITH THE ALREADY APPROVED CONDITIONS.**

A corrected bounded implementation may safely create exactly one 2527-row sidecar where:

1. every source row receives exactly one deterministic stable internal `Security_Key` seeded from `WS_ID`;
2. the generator is deterministic and collision-checked;
3. source `WS_ID`, ISIN, MIC, ticker, name, share-class/instrument and provenance attributes are copied as attributes/cross-checks rather than promoted to mutable key semantics;
4. `Company_Key` remains NULL unless independent existing repository evidence supports the `ISSUED_BY` relation;
5. no Company_Key is inferred from company/security name alone, ticker alone or fuzzy-name similarity;
6. all 1536 ISIN-missing rows receive a Security_Key but default to `SECURITY_UNRESOLVED` and `UNRESOLVED` confidence;
7. an ISIN-missing row cannot become `IDENTITY_OK` merely because WS_ID, MIC, ticker or name is populated;
8. distinct listings and share classes remain distinct Security_Key rows;
9. `MULTI_CLASS_REVIEW` and `MULTI_LISTING_REVIEW` remain review flags and do not automatically exclude rows;
10. source Research Partial bytes/data rows and Universe membership remain unchanged.

This v1 is useful even with a largely NULL Company_Key column because it creates the missing canonical security-key layer and a governed place to attach later issuer/company evidence without collapsing listings or contaminating Universe membership.

## 8. Corrected Implementation Guardrails

A later implementation gate must fail closed unless all of the following hold:

- input path is exactly `universe/research_partial_1633.csv`;
- input blob/source version is pinned at stage start;
- source row count is exactly 2527;
- output row count is exactly 2527;
- `Security_Key` count is 2527 and unique count is 2527;
- no input row is dropped or duplicated;
- all missing-ISIN rows remain non-`IDENTITY_OK` unless independent security-level evidence already present in repository proves the required identity state;
- unsupported Company_Key assignments = 0;
- name-only/ticker-only/fuzzy Company_Key assignments = 0;
- source CSV mutation = 0;
- Universe membership mutation = 0;
- P0 byte work reopened = NO;
- external evidence/provider/web work = NO;
- fundamentals acquisition = NO;
- Guru ranking = NO.

Focused tests must at minimum cover deterministic key stability, uniqueness/collision failure, missing-ISIN fail-closed behavior, nullable Company_Key behavior, distinct-listing preservation, distinct-share-class preservation, and no-touch source/membership invariants.

## 9. Manager Recommendation for the Next Stage

Recommended next stage, **not executed here**:

**Company/Security Mapping v1 Corrected Bounded Implementation Gate — IMPLEMENTATION ONLY — 2527-ROW SIDECAR — SECURITY_KEY FOR EVERY ROW — NULLABLE COMPANY_KEY — EXISTING REPOSITORY EVIDENCE ONLY — NO UNIVERSE WRITE — FOCUSED TESTS REQUIRED**

The corrected implementation must not add a new requirement that every row resolve a Company_Key before the security sidecar can exist.

## 10. No-Touch Verification

- mapping sidecar created: **NO**
- implementation code created: **NO**
- tests run: **NO**
- source CSV modified: **NO**
- Research Partial data changed: **NO**
- Universe membership changed: **NO**
- provider work: **NO**
- external evidence/web search: **NO**
- P0 byte work reopened: **NO**
- fundamentals acquired: **NO**
- Guru ranking run: **NO**

## 11. HARD STOP

**HARD STOP after manager decision.**

No corrected implementation gate is started automatically by this stage.
