# BR_IBRX100 B3 Classification-Tree Inversion / Exact-37 Sector Coverage Gate v0.65

## Verdict
**BLOCKED_B3_CLASSIFICATION_TREE_MACHINE_REPRODUCIBILITY**

BR_EXACT_37_CLASSIFICATION_COVERAGE_READY = **NO**.
READY / TOTAL = **0 / 37**.
AMBIGUOUS = **0**.
NOT_FOUND = **0**.
NOT_VERIFIED = **37**.
CLASSIFICATION NODES QUERIED = **0**.
DISTINCT SETORES = **0**.

## Predecessor lock
- Required start HEAD: 4e8151225f19ad1748c203b295e3ff699eabb7bf
- v0.64 exact-37 readiness: NO, 0/37 ready, 37 NOT_VERIFIED.
- v0.64 security -> company identity: 37/37 PASS.
- Taxonomy / level / code method: B3_CLASSIFICACAO_SETORIAL / SETOR_ECONOMICO / PDSC_SHA256_V1.
- v0.64 workflow/artifact: 36264343312 / 10913620188.
- v0.64 artifact digest: sha256:970d4c510642f5803ca4228fe2715d10661fc8733c7eb7fee5e1ad94d700678c.

## Tree-capture result
The official B3 root listed-companies application was machine-retrievable only as a partial rendered subsetor/segment slice. The official /classification endpoint was reachable but the bounded machine-readable extraction yielded an empty client-rendered shell. No complete official Setor Econômico -> Subsetor -> Segmento payload could be sealed.
A partial traversal would not prove that all official queryable leaf nodes were included, so fail-closed execution stopped before group-level coverage requests.

## Query encoding
The segment query encoding was independently reproduced for the existing official Agricultura and Minerais Metálicos examples. The verified mechanism is URLENCODE(BASE64(UTF8(encodeURIComponent(exact official label)))). No query-token guessing was used.
This does not cure the missing complete official node inventory.

## Coverage consequence
No company-driven requests and no 37-security page fanout were executed. The inherited 37 exact B3 company codes remain valid, but without a complete sealed taxonomy-node set the inversion cannot prove exhaustive company-code membership.
Smallest evidenced blocker: **B3_CLASSIFICATION_TREE_NOT_MACHINE_REPRODUCIBLE**.

## PDSC
PDSC generation is restricted to PROVABLY_MAPPABLE exact-37 rows. Since READY=0, no exact-37 PDSC code was generated; the determinism/collision evidence records NOT_APPLICABLE for this failed stage.

## Immutability
- Canonical BR mapping population: 0
- Sector RS: 0
- Other cohorts reopened: 0
- P0/P1/P2: 0/0/0
- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb
- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9
- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32

## Artifact binding
- Workflow run: 36266926685
- Workflow head: c1ed721118558f608fa18dc5ae080f768c76946e
- Artifact: 10914042556
- Artifact name: br-ibrx100-classification-tree-inversion-v0.65-36266926685
- Artifact digest: 0fcc27756c32156da0fa4be605f8dee1a2fa52fa3bd88aac2ecfc07355058146

## Next gate
**B3_CLASSIFICATION_TREE_NOT_MACHINE_REPRODUCIBLE**

Hard stop: no canonical sector metadata materialization and no other cohort opened.
