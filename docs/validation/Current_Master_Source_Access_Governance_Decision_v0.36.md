# Current Master Source Access Governance Decision v0.36

Status: DEV / RESEARCH / SHADOW – NOT PRODUCTIVE. This is an offline governance stage: no external requests, source discovery, price download, P0 execution, eligibility promotion, canonical import, or mutation of the Current Master and research partial.

## Binding decision

The official 14-segment source-superset target is retained. The Current Master remains a transparent 1633-row RESEARCH_PARTIAL, not a complete world universe. Eight segments are imported and six remain deferred. No waiver permits Wikipedia, ETF holdings, screeners, legacy Phase2 membership, name reconstruction, or unofficial constituent lists.

- FULL_SCAN_ALLOWED = false
- RESEARCH_PARTIAL_ALLOWED = true
- GLOBAL_SOURCE_SUPERSET_COMPLETE = false
- GLOBAL_SWING_U3K_FREEZE_ALLOWED = false
- PRODUCTIVE_AUTHORITY = false
- Automatic source retry = false

## Evidence-based blocked-segment governance

| Segment | Governance state |
| --- | --- |
| US_SP1500 | OFFICIAL_FULL_SOURCE_BROWSER_VISIBLE_RUNNER_BLOCKED |
| MX_IPC | OFFICIAL_CHANGE_DOCUMENTS_ONLY |
| KR_KOSPI200 | OFFICIAL_SOURCE_FOUND_DATA_ENDPOINT_NOT_RESOLVED |
| AU_ASX200 | OFFICIAL_FULL_SOURCE_BROWSER_VISIBLE_RUNNER_BLOCKED |
| NZ_NZX50 | OFFICIAL_ROUTE_SUBSCRIPTION_OR_LICENSE_REQUIRED |
| ZA_TOP40 | OFFICIAL_ROUTE_HTTP_BLOCKED |

Each segment is DEFERRED_UNTIL_EXTERNAL_ACCESS_CHANGE. It can be reopened only on documented evidence of a new free official full-membership route, a documented official API/download route, a changed access condition, legitimate licensed access, an official platform change, an explicit governance recheck, or preparation for a later productive promotion.

## Validation

The implementation records actual Git blob values for the frozen predecessor inputs, derives the imported segment counts from the actual Universe_Master sheet, requires 1633 master rows and reconciliation of all eight imported segments, and verifies the Current Master, research_partial_1633.csv, and its manifest are unchanged. It emits the six-row register, decision matrix, reopen-trigger register, operating scope, summary, checkpoint, manifest, and byte-identical v0.36 handoffs.

Next stage only: CURRENT_MASTER_RESEARCH_PARTIAL_1633_ELIGIBILITY_BASELINE_RECONCILIATION_AND_DATA_REFRESH_PLAN.
