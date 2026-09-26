# BR_IBRX100 Canonical Sector Key + Security Identity / Exact-37 Coverage Gate v0.64

## Verdict
**BLOCKED_EXACT_37_CLASSIFICATION_COVERAGE**

BR_SECTOR_IDENTITY_COVERAGE_READY = **NO**.
READY / TOTAL = **0 / 37**.
AMBIGUOUS = **0**.
NOT_FOUND = **0**.
NOT_VERIFIED = **37**.
SECTOR CODE METHOD = **PDSC_SHA256_V1**.

## Predecessor
- Required start HEAD: f0a67388740b17dd62b47f1163df76d503a9c50b
- v0.63 route: B3_LISTED_COMPANIES_CLASSIFICATION_SEARCH
- v0.63 route readiness: YES
- v0.63 access: PUBLIC_REPRODUCIBLE
- v0.63 classification content: PASS
- v0.63 source-native Sector_Code: NOT_AVAILABLE
- v0.63 workflow/artifact: 36258067350 / 10911387342
- v0.63 artifact digest: sha256:0ec10e147c619ec999af1b8de3dcd34b93d4fff29c3f6a96dd672bcb05446535

## G-SEC-03 forward governance
G-SEC-03 permits PDSC_SHA256_V1 when an authorized official taxonomy has an exact sector classification but no stable source-native Sector_Code. This changes forward governance only; historical v0.63 evidence is unchanged.
For absent native code the audit state is Source_Sector_Code=NULL, Sector_Code_Origin=PROJECT_DERIVED_CANONICAL, Sector_Code_Method=PDSC_SHA256_V1.

## Security -> company identity
All 37 Frozen BR rows are exact BVMF ordinary-share tickers already present in the official B3 IBrX100 source lineage. The official B3 share-code convention XXXXY defines the first four letters as the issuer/company code and 3 as ordinary share. The stage therefore derives the B3 company code from the exact official ticker without a company-name join.
Security -> company status: **37 / 37 PASS**.
Fuzzy matching: NO. Company-name joins: NO. Per-security web fanout: NO.

## Sector level binding
Sector_Taxonomy = B3_CLASSIFICACAO_SETORIAL.
Sector_Level = SETOR_ECONOMICO, bound to B3's first-level Setor Econômico. Subsetor and Segmento are not substituted for the canonical Sector level.

## PDSC_SHA256_V1 validation
The contract uses NFC only, U+001F separators, UTF-8 and full lowercase SHA-256 in the form PDSC1:<sha256>. Three official B3 sector-label method vectors were generated twice independently and were deterministic with zero collisions among the tested vectors.
These vectors validate the identifier method only; they are not claimed as exact-37 cohort coverage evidence.

## Exact-37 company -> classification coverage
The already-authorized B3 classification route remains official and reproducible at route-design level. However, the bounded execution environment did not yield a sealable row-complete all-company classification payload containing the exact official Sector_Name for every one of the 37 company codes.
The stage did not substitute 37 per-security web lookups. Consequently every row remains NOT_VERIFIED for exact company -> Sector_Name coverage, and no per-row PDSC canonical Sector_Code is generated.
Smallest evidenced blocker: **BR_EXACT_37_COVERAGE_INCOMPLETE**.

## Immutability / scope
- Canonical BR mapping population: 0
- Sector RS: 0
- Other cohorts reopened: 0
- P0/P1/P2: 0/0/0
- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb
- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9
- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32

## Artifact binding
- Workflow run: 36264343312
- Workflow head: 29bb27937d4ce043f0ec280c5107ac4316dae349
- Artifact: 10913620188
- Artifact name: br-ibrx100-sector-identity-coverage-v0.64-36264343312
- Artifact digest: 970d4c510642f5803ca4228fe2715d10661fc8733c7eb7fee5e1ad94d700678c

## Next gate
**BR_EXACT_37_COVERAGE_INCOMPLETE**

Hard stop: no canonical BR mapping materialization and no other cohort opened.
