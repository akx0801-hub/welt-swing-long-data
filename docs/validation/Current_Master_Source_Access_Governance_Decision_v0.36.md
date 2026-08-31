# Current Master Source Access Governance Decision v0.36

Status: DEV / RESEARCH / SHADOW – NOT PRODUCTIVE.

This offline stage records the governance decision after v0.35-r3 produced zero new reproducible official full-membership datasets. It makes no network requests, changes neither the 1633-row current master nor the research_partial_1633 snapshot, and does not run P0, Sector RS, a productive scan, or a global SWING_U3K freeze.

The official 14-segment source-superset target remains unchanged. Eight segments are present in the current master; US_SP1500, MX_IPC, KR_KOSPI200, AU_ASX200, NZ_NZX50 and ZA_TOP40 remain missing. No third-party membership fallback, ETF holding, Wikipedia, screener, legacy Phase2 substitution or reconstructed membership is permitted.

Every blocked segment is deferred until an explicit external-access-change trigger. Automatic retry is false. FULL_SCAN_ALLOWED is false; RESEARCH_PARTIAL_ALLOWED is true, provided outputs visibly retain the 8/14 coverage qualification.

The script validates frozen inputs, derives the eight imported segment counts from the actual Universe_Master sheet, verifies 1633 current-master rows, writes the six-row governance register and an auditable decision matrix, and verifies that the master and research snapshot hashes remain unchanged.

Next stage only: CURRENT_MASTER_RESEARCH_PARTIAL_1633_ELIGIBILITY_BASELINE_RECONCILIATION_AND_DATA_REFRESH_PLAN.
