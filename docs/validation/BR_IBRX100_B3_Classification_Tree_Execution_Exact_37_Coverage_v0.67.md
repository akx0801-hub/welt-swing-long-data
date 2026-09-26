# BR_IBRX100 B3 Classification Tree Execution / Exact-37 Coverage Gate v0.67

## Verdict
**PASS_BR_EXACT_37_CLASSIFICATION_COVERAGE**

BR_EXACT_37_CLASSIFICATION_COVERAGE_READY = **YES**.
READY / TOTAL = **37 / 37**.
AMBIGUOUS = **0**.
NOT_FOUND = **0**.
NOT_VERIFIED = **0**.
TREE NODES = **262**.
GROUP QUERIES EXECUTED / EXPECTED = **86 / 86**.
DISTINCT SETORES = **10**.
PDSC COLLISIONS = **0**.

## Predecessor
- Required start HEAD: a6c7e3db455d73c436142230bd466c64f2ac147d
- v0.66 verdict: PASS_B3_CLASSIFICATION_TREE_CONTRACT.
- Public tree contract: GET GetIndustryClassification/...; reproducible without authentication.
- v0.66 workflow/artifact: 36269159688 / 10915250534.
- v0.66 artifact digest: sha256:af7fe53a42cd199ff2b1a1edd98cb73d7535131b1e2135977c45a0853d12b5ae.
- Security -> B3 company code authority remains 37/37 from v0.64.

## Execution
- Setor count: 13.
- Subsetor count: 44.
- Segmento leaves: 90.
- Distinct Segmento labels: 86.
- Group requests successful: 86.
- Group requests failed: 0.
The exact tree payload, flattened hierarchy, segment collision audit, finite query inventory, response hashes and explicit B3 company-code membership are persisted as shadow evidence. No company-name or fuzzy matching is used.

## PDSC
Only PROVABLY_MAPPABLE rows receive PDSC_SHA256_V1. Raw B3 Setor Econômico labels are retained; NFC is derived only for the canonical name and hash input. Source_Sector_Code remains NULL unless B3 explicitly supplies one.

## Scope / immutability
- Canonical BR metadata materialization: 0.
- Sector RS: 0.
- Other cohorts reopened: 0.
- P0/P1/P2: 0/0/0.
- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.
- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9.
- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32.

## Blocker
**NONE**.

## Artifact binding
- Workflow run: 36270129434
- Workflow head: c3f0ff1a1232ee72bd193e66a0fc059954a47486
- Artifact: 10914754106
- Artifact name: br-ibrx100-b3-classification-tree-execution-v0.67-36270129434
- Artifact digest: 84d16a51b33ec4ff29375017244f498ab844d4a8621ee56c3a4d1736d5af1510

## Next gate
**BR_IBRX100 CANONICAL SECTOR METADATA MAPPING MATERIALIZATION GATE**

Hard stop: no canonical metadata materialization and no other cohort opened.
