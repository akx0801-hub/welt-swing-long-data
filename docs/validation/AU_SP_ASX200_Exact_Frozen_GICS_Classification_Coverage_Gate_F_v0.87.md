# AU_SP_ASX200 Exact Frozen GICS Industry-Group Classification Coverage Gate F v0.87

## Verdict
**PASS_AU_SP_ASX200_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_GATE_F**

AU_EXACT_FROZEN_GICS_CLASSIFICATION_COVERAGE_READY = **YES**.
FROZEN TOTAL = **63**.
CURRENT ASX DIRECTORY ROWS = **1833**.
EXACT SOURCE LINKS = **63**.
PROVABLY CLASSIFIED = **63**.
NOT_PROVABLY_CLASSIFIED = **0**.
NOT_FOUND = **0**.
AMBIGUOUS = **0**.
NOT_VERIFIED = **0**.
CONFLICT = **0**.
FORMAL LABEL BINDING = **63/63**.
SOURCE-NATIVE CODE COVERAGE = **63/63**.
NONFORMAL FROZEN EXPOSURE = **0**.
USED DISTINCT GICS CODES = **16**.
UNAUTHORIZED CODES = **0**.
PDSC GENERATED = **0**.

## Source drift
- BYTE_DRIFT: NO
- ROW_COUNT_DRIFT: NO
- SCHEMA_DRIFT: NO
- FROZEN_IDENTITY_DRIFT: NO
- FROZEN_CLASSIFICATION_DRIFT: NOT_EVALUABLE_FROM_V086_PERSISTED_IDENTITY_ONLY_EVIDENCE

## Scope
Gate F only. The exact v0.86 Frozen identity target was rebuilt from Frozen identity fields plus the governed Security_Key cohort sidecar and required to match the predecessor target exactly. One fresh official ASX company-directory CSV snapshot was joined by exact ASX code only. Formal labels and source-native four-digit codes came solely from persisted v0.85 MSCI authority. No company-name linkage, fuzzy/semantic mapping, ticker-history repair, PDSC, MSCI network request, Gate G/H, canonical materialization, other cohort, Sector RS or P0/P1/P2 was executed.

## Blocker
**NONE**.

## Artifact binding
- Workflow run: 36392661784
- Workflow head: bf18216d914fcf482bc531abd925a4a9898aacf9
- Artifact: 10956817563
- Artifact digest: sha256:961c68520689e978945a550b4d05b7a2e698f5b890fc072caecffb6a95e186bc

## Next gate
**AU_SP_ASX200 PROVENANCE GATE G**

Hard stop applied.
