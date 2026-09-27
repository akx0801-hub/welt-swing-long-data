# IN_NIFTY50 NSE Indices Sectoral-Distribution Data Contract / Gate-F Resolution v0.73

## Verdict
**BLOCKED_IN_NIFTY50_GATE_F_APPLICATION_CONTRACT_RESOLUTION**

IN_EXACT_45_SECTOR_CLASSIFICATION_COVERAGE_READY = **NO**.
CLASSIFIED / TOTAL = **0 / 45**.
AMBIGUOUS = **0**.
NOT_FOUND = **0**.
NOT_VERIFIED = **45**.
CONFLICT = **0**.
APPLICATION CONTRACT = **https://liveindexsa.niftyindices.com/jsonfiles/Basic%20Industry/SectorialIndexDataNIFTY%2050_BasicIndustry.js; https://liveindexsa.niftyindices.com/jsonfiles/Industry/SectorialIndexDataNIFTY%2050_Industry.js; https://liveindexsa.niftyindices.com/jsonfiles/MacroEconomicSector/SectorialIndexDataNIFTY%2050_MacroEconomicSector.js; https://liveindexsa.niftyindices.com/jsonfiles/Sector/SectorialIndexDataNIFTY%2050_Sector.js**.
BOUND CLASSIFICATION LEVEL = **NOT_VERIFIED**.
DISTINCT CLASSIFICATIONS = **15**.
SOURCE-NATIVE CODE COVERAGE = **0 / 45**.

## Scope
This stage preserves the v0.72 exact-string result and resolves only the remaining Gate-F application-contract question. v0.70 identity authority remains 45/45 and is not rerun. NSE EQUITY_L and the NIFTY constituent CSV are not refetched.
Only public NSE Indices application assets and requests are permitted. Browser interception blocks non-niftyindices.com network requests. No authentication or CAPTCHA bypass is used.

## Application contract evidence
- Browser capture status: PASS
- Candidate public application contracts: 4
- Derived application membership rows: 0
- Independent public replay: PASS

The level parameter contract, response schema, security membership, CSV-vs-application assignments, application node identities, and node-to-taxonomy code bindings are persisted separately. Raw response bodies are not persisted.

## Scope boundary
No company-name joins, fuzzy matching, semantic inference, cross-taxonomy mapping, PDSC fallback, per-security fanout, Gate H promotion, canonical materialization, Sector RS, or P0/P1/P2 execution occurred.

## Immutability
- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.
- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9.
- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32.
- BR canonical semantic SHA unchanged: bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed.
- Canonical READY remains 37/1425.

## Blocker
**NIFTY_SECURITY_CATEGORY_MEMBERSHIP_NOT_REPRODUCIBLE**.

## Artifact binding
- Workflow run: 36312324586
- Workflow head: 8b4c7479774d08382a671b417f5cd67f6986af17
- Artifact: 10928868468
- Artifact name: in-nifty50-sectoral-distribution-contract-v0.73-36312324586
- Artifact digest: 3ccfe23226841406430e2044bda6378168e5894fc0777448cbb66d76b0e9ab79

## Next gate
**NIFTY_SECURITY_CATEGORY_MEMBERSHIP_NOT_REPRODUCIBLE**

Hard stop: no Gate H, canonical materialization, Sector RS, P0/P1/P2, or next cohort execution.
