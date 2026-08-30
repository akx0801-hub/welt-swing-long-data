## Current Master Remaining Missing Segment Official Source Materialization v0.35

Stage CURRENT_MASTER_REMAINING_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION is DEV / RESEARCH / SHADOW only. It checks the six missing target segments solely against official source families: US_SP1500, MX_IPC, KR_KOSPI200, AU_ASX200, NZ_NZX50 and ZA_TOP40.

It never mutates universe/Welt-Swing-Universe-Master-v2.0.xlsx or universe/research_partial_1633.csv. It performs no P0, Sector RS, SWING_U3K_FROZEN, eligibility promotion, productive scan or Alpha Vantage use.

### Source governance

Only official index-administrator, exchange, registry or official data-portal routes are requested. Each runner request is bounded, assigned to one segment/source ID and recorded without cookies, tokens or credentials. A visible browser page is not a reproducible membership export.

A segment may progress only with FULL_OFFICIAL_MEMBERSHIP_MATERIALIZED: a current official full dataset, positive row count, unique official security codes and a reproducible runner route. Change announcements, top-ten displays, methodologies, ETF holdings, historical lists and inferred reconstructions are not membership evidence.

### Frozen inputs

The workflow pins the pre-stage baseline commit 63be0bba22911cbda752062862f6ea28127af913 and evaluates actual Git blobs for each required input against that baseline. This prevents silent input drift while keeping the recorded blob hashes reproducible from Git itself.

### Expected v0.35 outcome

The v0.35 retry is intentionally fail-closed. Current official evidence supports these outcomes unless a reproducible full official export is demonstrated in-run:

- US_SP1500: full export login/license blocker.
- MX_IPC: official change documents only.
- KR_KOSPI200: official platform found, constituent endpoint unresolved.
- AU_ASX200: official full list visible but no reproducible export.
- NZ_NZX50: subscription/license required.
- ZA_TOP40: subscription/client-portal route required.

The global stage remains PARTIAL. If no segment is materialized, the next stage is CURRENT_MASTER_REMAINING_SOURCE_ACCESS_REMEDIATION_AND_GOVERNANCE_DECISION; otherwise it is the identity-reconciliation stage.
