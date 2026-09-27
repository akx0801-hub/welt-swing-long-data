# IN_NIFTY50 NSE Indices Classification Structure Extraction / Level + Code Binding / Gate-F Repair v0.72

## Verdict
**BLOCKED_IN_NIFTY50_GATE_F_REPAIR**

IN_EXACT_45_SECTOR_CLASSIFICATION_COVERAGE_READY = **NO**.
CLASSIFIED / TOTAL = **0 / 45**.
AMBIGUOUS = **0**.
NOT_FOUND = **0**.
NOT_VERIFIED = **45**.
CONFLICT = **0**.
BOUND CLASSIFICATION LEVEL = **NOT_VERIFIED**.
DISTINCT CLASSIFICATIONS = **15**.
SOURCE-NATIVE CODE COVERAGE = **0 / 45**.
PDF EXTRACTION = **PASS: pypdf 5.9.0, 23 pages, deterministic structural SHA d431587f5f686b8432bc57755a8fe6aef232fed49fb858cf7e905b3318687173**.

## v0.71 evidence correction
The narrative sentence claiming every observed NIFTY Industry label had already been exact-bound to one unique Ind_Code is explicitly classified as erroneous non-authoritative narrative text. The structured v0.71 evidence remains authoritative: zero exact unique bindings, level NOT_VERIFIED, and zero source-native code coverage. v0.71 history was not rewritten.

## Extraction scope
The stage consumes the persisted v0.70 identity authority and v0.71 exact-45 derived classification rows. It does not rerun Gate E and does not refetch ind_nifty50list.csv or use NSE EQUITY_L.
The official NSE Indices classification structure PDF is the only market/reference retrieval. Raw PDF redistribution rights remain NOT_VERIFIED, so the raw PDF is not persisted.

## Parser environment
- Tool: pypdf 5.9.0
- PDF SHA-256: 8ae58cbd10d7dd5184d76cfec6486f91c019026c8de329432b69c54ff7235f8b
- Matches v0.71 PDF SHA: YES
- Extracted-text deterministic: YES
- Structural-output deterministic: YES
- Page count: 23

## Scope boundary
No PDSC fallback, company-name join, fuzzy matching, cross-taxonomy mapping, per-security fanout, Gate H promotion, canonical IN partition, Sector RS, or P0/P1/P2 execution occurred.

## Immutability
- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.
- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9.
- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32.
- BR canonical semantic SHA unchanged: bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed.
- Canonical READY remains 37/1425.

## Blocker
**NIFTY_CLASSIFICATION_LEVEL_BINDING_NOT_VERIFIED**.

## Artifact binding
- Workflow run: 36309975985
- Workflow head: 4407febe03589fe8b6e22925c51b10e0501d7458
- Artifact: 10929365141
- Artifact name: in-nifty50-nse-classification-structure-repair-v0.72-36309975985
- Artifact digest: 8c3fb77305adcb7e2321aed34805ab5525afc176d3a7b7b4fa26420ca649ebba

## Next gate
**NIFTY_CLASSIFICATION_LEVEL_BINDING_NOT_VERIFIED**

Hard stop: Gate H not executed; no canonical materialization and no next cohort.
