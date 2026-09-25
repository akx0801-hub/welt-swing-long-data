# P0 Frozen-1425 Price-Cache Currentness / Ingestion Remediation v0.45

## Verdict
- Stage remediation: **PASS**
- P0_PRICE_CACHE_READY: **NO**
- Final cache: **1415 READY / 10 QUARANTINE**
- P0 was **NOT RUN**.

## Authority and population
- Required start HEAD: `87efb302406e8e6297b21a2ea8efdbf6ef19cbf6`
- Frozen members: 1425
- Frozen SHA-256: `54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb`
- Current 522-evidence ingestion: 431
- Stale refresh population: 994
- Population reconciliation: 431 + 994 = 1425

## Acquisition
- Refreshed via YFINANCE_FREE: 994 attempted, 992 READY, 2 non-ready.
- Reused without market re-download: 431 members; 423 READY, 8 non-ready.
- Provider batch calls including retries: 11.
- Rescue batches: 0; repair symbol attempts: 2.
- Alpha Vantage calls: 0.

## Final cache states
- READY: 1415
- QUARANTINE: 10
- Missing Frozen identities: 0
- Unexpected identities: 0

## Exact non-ready securities
- `WSSEC:WS:XASX:ANZ` / `WS:XASX:ANZ` / XASX:ANZ / provider `ANZ.AX`: **STRICT_OHLC_RELATION_FAIL**.
- `WSSEC:WS:XASX:BSL` / `WS:XASX:BSL` / XASX:BSL / provider `BSL.AX`: **STRICT_OHLC_RELATION_FAIL**.
- `WSSEC:WS:XASX:BXB` / `WS:XASX:BXB` / XASX:BXB / provider `BXB.AX`: **STRICT_OHLC_RELATION_FAIL**.
- `WSSEC:WS:XASX:CBA` / `WS:XASX:CBA` / XASX:CBA / provider `CBA.AX`: **STRICT_OHLC_RELATION_FAIL**.
- `WSSEC:WS:XASX:NXT` / `WS:XASX:NXT` / XASX:NXT / provider `NXT.AX`: **STRICT_OHLC_RELATION_FAIL**.
- `WSSEC:WS:XASX:PME` / `WS:XASX:PME` / XASX:PME / provider `PME.AX`: **STRICT_OHLC_RELATION_FAIL**.
- `WSSEC:WS:XASX:QAN` / `WS:XASX:QAN` / XASX:QAN / provider `QAN.AX`: **STRICT_OHLC_RELATION_FAIL**.
- `WSSEC:WS:XASX:SDF` / `WS:XASX:SDF` / XASX:SDF / provider `SDF.AX`: **STRICT_OHLC_RELATION_FAIL**.
- `WSSEC:WS:XNAS:ECHO` / `WS:XNAS:ECHO` / XNAS:ECHO / provider `ECHO`: **SUSPICIOUS_RETURN_NEEDS_REPAIR**.
- `WSSEC:WS:XNAS:MRNA` / `WS:XNAS:MRNA` / XNAS:MRNA / provider `MRNA`: **SUSPICIOUS_RETURN_NEEDS_REPAIR**.

Eight AU1 rows are quarantined by the explicit strict OHLC relation check on persisted 522 evidence. Two US1 rows remain quarantined for suspicious returns after the bounded repair pass.

## Governance
- Frozen membership unchanged.
- No P0/P1/P2 execution.
- No feature, Home-Market-RS, Sector-RS or parameter promotion.
- No Scalable calls.
- No Alpha Vantage.
- LONG DEV remains DEV / RESEARCH / SHADOW.

## Runtime cache lineage
- Workflow run: `36138138825`
- Runtime artifact: `10865594502`
- Artifact digest: `sha256:d5dfeb8250949632d0982ad7272046e9dbca24f0ee650eb8a9c3ba7dc1c29fab`
- Runtime SQLite SHA-256: `a245c23c7644589ef6c79195b61c13dfdd47bd8b89b9f3ee923de205a73541c0`
- Runtime SQLite remains in the Actions artifact; it is not committed to the repository.

## Next gate
**P0 FROZEN-1425 NON-READY 10 PRICE-QA EXACT REMEDIATION GATE**

The next gate is limited to the exact ten quarantined identities. It must not run P0 or alter Frozen membership.
