# AU_SP_ASX200 Park / Post-Park Reselection / TW_TW50 Gate B v0.90

## Verdict
**BLOCKED_TW_TW50_OFFICIAL_SECTOR_BULK_SOURCE_GATE_B**

## AU external-authorization park
- AU park state: **PARKED_EXTERNAL_AUTHORIZATION**
- Technical gates A-G: **PASS**
- Gate H: **BLOCKED**
- Primary blocker: **EXPLICIT_ASX_SOURCE_POLICY_OPERATIONAL_RESTRICTION**
- Independent GICS blocker: **EXPLICIT_GICS_SOURCE_POLICY_OPERATIONAL_RESTRICTION**

## Deterministic reselection
- Selected cohort: **TW_TW50**
- Basis: same consecutive resolved depth (1) and earliest unresolved gate B as CN_CSI300; smaller Frozen row count 49 vs 294

## TW_TW50 Gate B
- TW_OFFICIAL_SECTOR_BULK_SOURCE_READY: **NO**
- Official source: https://research.ftserussell.com/analytics/factsheets/Home/DownloadConstituentsWeights/?indexdetails=TW50
- Source composition: NONE_VERIFIED
- Bulk route type: OFFICIAL_STATIC_LINKED_BULK_DOWNLOAD
- Public / reproducible: YES
- Direct HTTP replay: FAIL
- Row-level security records: NO
- Security identifier: NOT_AVAILABLE (NOT_AVAILABLE)
- ICB Industry Group code field: NOT_AVAILABLE
- ICB Industry Group name field: NOT_AVAILABLE
- ICB level binding: NOT_VERIFIED
- Per-security fanout: 0
- Frozen-49 linkage runs: 0

## Blocker
**TWSE_TAIWAN50_BULK_CONSTITUENT_ROUTE_NOT_REPRODUCIBLE**.

No TW Gate E/F/H, no Frozen-49 row-level linkage, no canonical materialization, no Sector RS and no P0/P1/P2 were executed.

## Artifact binding
- Workflow run: 36414129933
- Workflow head: 6c8a6f589251c5ac271c1f98ea2db756cb5ccd45
- Artifact: 10966961769
- Artifact digest: sha256:91d535cce36d6e8f0f3b0e314b721c366751ff62962773b6ae9fac5db42242f9

## Next gate
**TW_TW50 SOURCE-ROUTE PARK / ACTIVE-COHORT RESELECTION MANAGER GATE**

Hard stop applied.
