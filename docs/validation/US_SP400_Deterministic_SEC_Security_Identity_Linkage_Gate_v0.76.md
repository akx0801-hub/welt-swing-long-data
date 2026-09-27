# US_SP400 Deterministic SEC Security Identity Linkage Gate + IN_NIFTY50 Park v0.76

## Governance
G-SEC-06 parks IN_NIFTY50 as PARKED_EXTERNAL_AUTHORIZATION. Its proven technical gates A-G and Gate-F 45/45 remain unchanged; Gate H remains blocked by EXPLICIT_SOURCE_POLICY_OPERATIONAL_RESTRICTION. Parking creates no canonical rows and excludes IN_NIFTY50 from automatic next-cohort selection.

Applying the persisted v0.69 deterministic selection rule after excluding BR_IBRX100 (canonical READY) and IN_NIFTY50 (parked) selects US_SP400. US_SP400 and US_SP500 both have four consecutive resolved gates A-D, and 368 rows wins the row-count tie-break against 372.

## Verdict
**BLOCKED_US_SP400_DETERMINISTIC_SEC_SECURITY_IDENTITY_LINKAGE**

US_SP400_DETERMINISTIC_SEC_IDENTITY_READY = **NO**.
LINKED / TOTAL = **0 / 368**.
AMBIGUOUS = **0**.
NOT_FOUND = **368**.
NOT_VERIFIED = **0**.
CONFLICT = **0**.

## Identity route
SEC exact ticker + SEC exact exchange -> ISO 10383 exact ACRONYM -> operating MIC -> Frozen exact (Primary_Ticker, Primary_MIC) -> WS_ID

The SEC ticker/exchange file URL is discovered from official SEC EDGAR documentation. Exchange-to-MIC authority is taken only from the official ISO 10383 MIC dataset discovered from the ISO 20022 MIC landing page. The join never uses company names or fuzzy matching; CIK is retained as issuer-reference evidence and share classes are not collapsed.

## Exchange-to-MIC authority
https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv / exact SEC exchange value to ISO ACRONYM, unique operating MIC

## SEC fair access
SEC requests use a descriptive project User-Agent/contact URL, bounded bulk requests, no per-security fanout, and no polling or throttling bypass. Request URLs, statuses, hashes, and timestamps are persisted in the external request ledger.

## Scope boundary
No US Gate F, SIC promotion, canonical materialization, US_SP500 execution, other cohort execution, NSE request, Sector RS, P0/P1/P2, price/news/trading analysis, or forbidden provider call occurred.

## Immutability
- Frozen SHA unchanged: 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.
- v0.57 Feature SHA unchanged: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9.
- v0.58 Home-Market-RS SHA unchanged: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32.
- BR canonical semantic SHA unchanged: bd975af67f46d6961f50480fe3eea391bd807d6c65c1a376717fbd0c07d19aed.
- IN Gate-F remains 45/45; IN canonical rows remain 0.
- Global canonical READY remains 37/1425.

## Blocker
**SEC_TICKER_EXCHANGE_BULK_ROUTE_NOT_REPRODUCIBLE**.

## Artifact binding
- Workflow run: 36322252802
- Workflow head: 660bd5ba5ce12a7958317bf81388ad753dc37f2b
- Artifact: 10932404865
- Artifact name: us-sp400-sec-identity-linkage-v0.76-36322252802
- Artifact digest: d43417c1e101e0cee2da785ea0c78f80305f9f0d8cd03e2498017427259b0f34

## Next gate
**SEC_TICKER_EXCHANGE_BULK_ROUTE_NOT_REPRODUCIBLE**

Hard stop: no US Gate F, canonical metadata materialization, US_SP500 execution, Sector RS, or P0.
