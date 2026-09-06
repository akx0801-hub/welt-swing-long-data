# Canada Rebuild Post-Build Manager Gate

## Decision

**CANADA REBUILD POST-BUILD MANAGER GATE — PASS**

**RECOMMENDATION A — TARGETED CURRENT EVIDENCE ACQUISITION**

**NEXT AUTHORIZED STAGE: Canada Rebuild Targeted Current Evidence Acquisition — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

This is a manager decision only. It authorizes neither a second rebuild nor any Universe, Membership, Research Partial, Strict, Frozen, Mapping, Admission, Integration, History, Liquidity or Eligibility write.

## Start and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Verified start HEAD: `3bb986f07614e42ec6c3af8dcbb51a0e645b56bd`
- Commit: `Canada rebuild admission build controlled sidecar only`
- Authorized stage: Canada Rebuild Post-Build Manager Gate — READ-ONLY
- Research Partial: 2527
- Strict: 759
- Frozen: 0

## Existing Build confirmation

The existing Canada Rebuild Admission Build is present and was not rerun.

| Measure | Count |
|---|---:|
| Candidate count | 217 |
| ADMIT | 0 |
| REVIEW | 215 |
| EXCLUDE | 2 |
| Final-status sum | 217 |
| Verified ISIN | 0 |
| Verified Share Class | 0 |
| Verified Instrument Type | 0 |
| Current ACTIVE listings freshly verified | 0 |
| Primary MIC/Ticker from source lineage | 217 |
| Corporate-action cases | 2 |

The two exclusions are ARX and SES, for which official S&P corporate-action notices document removal/acquisition treatment. No successor security was silently added. The other 215 candidates remain REVIEW.

Legacy Canada remains a separate historical baseline of 217 rows and is unchanged.

## Meaning of the build result

The result does not establish that the 217 securities are false or that Canada is unsuitable. It establishes that the existing snapshot and available listing lineage do not, by themselves, provide current full membership reconciliation, current ACTIVE listing verification, exact ISINs, exact Share Classes or instrument types.

The result is therefore a source/evidence coverage failure, not an admission failure of every individual security.

## Historical evidence results

| Stage | Result |
|---|---|
| Legacy Conversion / Identity Gate | 0/217 conversion-ready |
| Exact Evidence v2 | 0/217 EVIDENCE_READY |
| Targeted Manual Recovery | 0/30 RECOVERY_READY |
| Current Rebuild Build | 0/217 ADMIT |

The previous attempts used the same fundamental limitation: listing/ticker lineage was available, but reproducible security-level identifier and class evidence was not retained. A second full run or another arbitrary 217-row search is therefore rejected.

## Option A — Targeted Current Evidence Acquisition

A narrowly bounded Current-Evidence stage remains justified because the rebuild has a materially different evidence starting point:

1. The current S&P/TSX Composite characteristics page was observed with 217 constituents as of 2026-08-31.
2. Current TMX/TSX listing-directory evidence is available as the official listing path.
3. Official S&P corporate-action notices were available for current removal/acquisition cases.
4. The next stage can select only a reproducible, documented subset and require current membership, ACTIVE listing and security-level identity from the outset.
5. The stage can focus on simple XTSE Common/Ordinary candidates where issuer filings and security documents are most likely to identify the exact class and ISIN.

This is not a second Build. It must not regenerate the 217-candidate population or change the policy.

### Required bounded scope

- Target size: 20–50 candidates; preferred operating range 20–30.
- Selection must be deterministic and documented before research.
- Selection may prioritize simple Common/Ordinary XTSE primary listings, current membership evidence, no corporate-action warning, no obvious class ambiguity and accessible issuer/filing evidence.
- No fame-based list and no discretionary cherry-picking.
- Every selected case must be processed to a final status; unresolved cases remain REVIEW.

### Hard identity standard

No policy relaxation is permitted. A candidate can become ADMIT only with:

- current S&P/TSX Composite membership evidence;
- current ACTIVE XTSE primary listing;
- exact issuer, Security and Share Class;
- exact Instrument Type;
- reproducible valid ISIN with format and Luhn checks;
- semantic ISIN/Security/Class match;
- verified Primary_MIC and Primary_Ticker;
- no unresolved corporate action;
- no TRUE_IDENTITY_CONFLICT.

CUSIP, issuer-only matches, ticker-only matches and silent Share-Class mapping remain invalid. Alpha Vantage remains prohibited.

### Source-path assessment

- Current membership: feasible for targeted cases if the official S&P reference or a clearly documented institutional current Composite source is available. A partial public export cannot support silent full-population claims.
- Current ACTIVE listing: feasible through TMX/TSX official listing evidence, but must be freshly documented per selected case.
- Exact Share Class and Instrument Type: feasible selectively through issuer IR, annual reports, prospectuses and SEDAR+ filings; not guaranteed for every case.
- Exact ISIN: feasible selectively through issuer/regulatory or institutional identifier evidence, with semantic matching required.
- Corporate actions: feasible through official S&P notices and issuer/regulatory documents.
- Primary MIC/Ticker: feasible through official exchange evidence; existing lineage alone is insufficient for current admission.

### Expected economics

- Expected manual cost: HIGH
- Expected scalability: LIMITED
- Expected recovery probability for a carefully selected subset: MEDIUM
- Expected strategic value: MEDIUM to HIGH

The stage is justified only as a bounded yield test. It must stop at the pre-declared target size. A successful result would create evidence for a later Manager Gate, not an automatic admission or integration.

## Option B — Park Canada

Parking is operationally safe and remains the fallback if the targeted stage cannot obtain a reproducible current membership source or current security-level identifier path.

Parking would preserve:

- Legacy Canada: 217 unchanged;
- Rebuild sidecars: retained;
- ADMIT: 0;
- REVIEW: 215;
- EXCLUDE: 2.

Parking would avoid further cost, but it would leave a potentially valuable developed-market diversification opportunity untested under current-source evidence rules. Because the current build identified materially better current-source paths than the earlier legacy-recovery work, immediate parking is not selected.

## Qualitative-difference test

The difference is concrete, not merely “search more carefully”:

- previous recovery attempted to resolve an existing legacy membership;
- this stage would resolve a bounded subset of a current S&P/TSX Composite rebuild;
- current S&P characteristics and official corporate-action notices provide a current temporal anchor;
- TMX/TSX current listing verification and issuer/SEDAR+ security documents are applied as admission prerequisites;
- no legacy ticker or legacy row is treated as identity truth.

If these current-source paths are not technically reproducible at the next stage, that stage must fail closed and return to a Manager Gate.

## Final recommendation

**RECOMMENDATION A — TARGETED CURRENT EVIDENCE ACQUISITION**

The 217-row result does not justify another full run. However, the current-source architecture is sufficiently different to justify one tightly bounded, sidecar-only evidence stage. The purpose is to test whether a small objectively selected subset can produce real ADMIT-quality identities under the unchanged hard gates.

No second Build, full-217 rerun or automatic Batch 2 is authorized.

## Exact next stage

**Canada Rebuild Targeted Current Evidence Acquisition — READ-ONLY / SIDECAR ONLY / NO UNIVERSE WRITE**

The next stage may create only its own selection, evidence and analysis sidecars. It may not modify the 217 legacy rows, the existing rebuild sidecars, Research Partial, Strict, Frozen or any Universe/Data Master.

## Quality gates

- G0 Correct origin/main HEAD — PASS
- G1 Correct authorized Manager stage — PASS
- G2 Existing Build recognized; no duplicate Build — PASS
- G3 Candidate count 217 verified — PASS
- G4 ADMIT 0 / REVIEW 215 / EXCLUDE 2 acknowledged — PASS
- G5 Current membership reconciliation gap acknowledged — PASS
- G6 Current ACTIVE listing gap acknowledged — PASS
- G7 ISIN/Share Class/Instrument gaps acknowledged — PASS
- G8 Historical failed evidence paths considered — PASS
- G9 Option A evaluated — PASS
- G10 Option B evaluated — PASS
- G11 Qualitative-difference test applied — PASS
- G12 Evidence economics evaluated — PASS
- G13 Opportunity cost evaluated — PASS
- G14 Exactly one recommendation selected — PASS
- G15 Exact next stage defined — PASS
- G16 No Universe/Data write — PASS
- G17 No follow-on stage executed — PASS

## No-touch confirmation

No Canada Build was rerun. No full-217 evidence rerun was performed. No Membership, Rebuild sidecar, Research Partial, Strict, Frozen, Universe/Data Master, Mapping, History, Liquidity, Eligibility, Scan/U3K or v7.2 file was changed.

**CANADA REBUILD POST-BUILD MANAGER GATE — PASS**

**RECOMMENDATION A — TARGETED CURRENT EVIDENCE ACQUISITION**
