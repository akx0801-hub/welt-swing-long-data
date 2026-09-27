# AU_SP_ASX200 Dynamic Directory Data-Route Repair / Gate C Completion v0.82

## Verdict
**BLOCKED_AU_SP_ASX200_SOURCE_NATIVE_TAXONOMY_IDENTITY_GATE_C**

AU_SOURCE_NATIVE_TAXONOMY_IDENTITY_READY = **NO**.
DYNAMIC DIRECTORY ROUTE = **FAIL**.
PUBLIC BROWSER REPRODUCIBLE = **YES**.
DIRECT HTTP REPLAY = **NOT_APPLICABLE**.
DATA ROUTE TYPE = **DETERMINISTIC_FINITE_PAGINATION**.
DATA RECORDS = **0**.
CLASSIFICATION FIELD = **NOT_AVAILABLE**.
TAXONOMY IDENTITY = **NOT_VERIFIED**.
TAXONOMY OWNER = **NOT_VERIFIED**.
FORMAL LEVEL = **NOT_VERIFIED**.
VERSION STATUS = **NOT_VERIFIED**.
FIELD→TAXONOMY BINDING = **NOT_VERIFIED**.
GICS FIELD BINDING = **NOT_VERIFIED**.
UPSTREAM PROVIDER ATTRIBUTION = **NOT_VERIFIED**.

## Runtime route evidence
Two independent fresh public browser contexts reproduced the same logical directory data route and schema contract.
RUN 1 route: GET https://asx.api.cmfyapp.com/asx-research/1.0/companies/directory ?includeFilterOptions&itemsPerPage&order&orderBy&page&recentListingsOnly.
RUN 2 route: GET https://asx.api.cmfyapp.com/asx-research/1.0/companies/directory ?includeFilterOptions&itemsPerPage&order&orderBy&page&recentListingsOnly.
Both sessions use fresh temporary browser profiles, no pre-existing cookies, no authentication and no proxy. Only ordinary page-generated runtime traffic and the bounded permitted interaction sequence were observed.

## Taxonomy identity
Gate C remains fail-closed. No generic Industry-like field, provider credit or ASX GICS usage elsewhere was promoted into a taxonomy binding without exact field-level evidence.

## Historical Gate B / current route
HISTORICAL_GATE_B = **PASS_INHERITED**.
CURRENT_ROUTE_REPRODUCIBILITY = **FAIL**.
CURRENT_AUTHORITY_IMPACT = **SOURCE_ROUTE_REVIEW_REQUIRED**.
Historical evidence was not rewritten.

## Hard scope
AU Gate D/E/F remain NOT_EVALUATED. No Frozen-63 linkage, classification attachment, PDSC, canonical materialization, park/reselection execution, next cohort, Sector RS or P0/P1/P2 occurred. IN_NIFTY50, JP_N225, US_SP400 and US_SP500 park states are unchanged. Global canonical READY remains 37/1425.

## Blocker
**ASX_DIRECTORY_DYNAMIC_DATA_ROUTE_NOT_REPRODUCIBLE**.

## Artifact binding
- Workflow run: 36343377368
- Workflow head: 4776342d524bdc096bcf8786fd4bfe3533bb0ba2
- Artifact: 10940220470
- Artifact name: au-asx200-dynamic-directory-gate-c-v0.82-36343377368
- Artifact digest: sha256:1c401854687ebd9cbe4af89422960ed6cbea2817bb90c5771cca3ee7032110c0

## Next gate
**AU_SP_ASX200 SOURCE-ROUTE PARK / ACTIVE-COHORT RESELECTION MANAGER GATE**

Hard stop applied after persistence and artifact binding.
