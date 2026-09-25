# P0 Frozen-1425 ASX-8 Official / Licensed EOD Acquisition v0.50

## Gate verdict
**PASS WITH ACCESS BLOCKED**

Required start HEAD: `66df44cc466950692d00e0a05ae8259804e2decd`.

Scope is exactly ANZ, BSL, BXB, CBA, NXT, PME, QAN and SDF for **2024-11-15**. No cache, Frozen membership, provider mapping, QA rule or runtime state was mutated.

## ASX official access finding
ASX ReferencePoint Daily Official List is the strongest direct authority. ASX documents the product as an official end-of-day trade/quote service and its manual exposes trade-based **First, High, Low, Last/Previous Last** plus cumulative sales volume/value in EOD snapshots. ASX Trade documentation defines opening as the first on-market sale, high/low as the highest/lowest on-market traded prices and last as the last on-market traded price.

ASX also states that historical price data covers every ASX market. However, the exact 2024-11-15 Daily Official List rows are not publicly exposed through the current environment. ReferencePoint is delivered through subscriber channels such as ASX Online B2B and historical price access is a licensed/contact product.

Result: **OFFICIAL_DATA_ACCESS_BLOCKED**. No values were guessed or substituted.

## Licensed vendor paths
ASX's own Vendor and ISV list identifies both **EODData** and **EOD Historical Data (EODHD)** as End-of-Day ASX price-data vendors.

EODData documents a commercial historical feed containing Symbol, Date, Open, High, Low, Close and Volume. Historical access requires membership/purchase and its terms restrict business use/redistribution without the appropriate licence.

EODHD documents an ASX EOD product with 30+ years of daily data and an API returning date/open/high/low/close/adjusted_close/volume. EODHD's ASX page states it is an official ASX data provider with a direct redistribution licence, but individual access still requires an API token and appropriate personal/commercial/exchange rights. Its free access does not cover the 2024-11-15 target date.

No entitled credential for either vendor is connected to this environment, so no licensed exact-date row was acquired and no licensed raw record was stored in the repo.

## Acquired complete OHLC
No official or licensed complete target row was acquired in this gate.

One pre-existing independent secondary complete row remains available for the PME control:
- PME 2024-11-15: O 207.24 / H 209.86 / L 205.60 / C 209.86 / Volume 103408.
It is internally coherent and continues to confirm that the challenged provider's PME High/Volume are inconsistent. Its methodology/licensing is not sufficient for controlled cache replacement.

CBA retains only the 155.13 transaction-price corroboration. QAN retains only the independent 8.89 close corroboration.

## Rewrite eligibility
CACHE_REWRITE_EVIDENCE_READY = **NO** for all eight.

The distinction remains:
1. Yahoo/provider defect may be evidenced.
2. A better row may exist.
3. A row is not rewrite authority until complete, same-date/same-identity/same-currency/same-basis, internally valid, sufficiently authoritative/licensed and provenance-safe.

PME satisfies (1) and has a complete secondary row for (2), but not (3).

## Runtime state
v0.48 remains authoritative and unchanged:
- SQLite SHA-256: `8973ff393db23c7e2d456502c2a71f085f17407dc5ed244dcc04d566c87d4063`
- bytes: 144216064
- READY: 1417
- QUARANTINE: 8
- total: 1425
- P0_PRICE_CACHE_READY = NO

## Next gate
**P0 FROZEN-1425 ASX-8 EODHD LICENSED EXACT-DATE ENTITLEMENT / CREDENTIALLED ACQUISITION GATE**

This is the smallest concrete licensed path identified: obtain an entitled EODHD access token/plan and confirm rights for the intended internal runtime/repository evidence use, then request only the eight exact 2024-11-15 EOD rows. Do not execute that gate automatically.
