# Current Master Research Partial 2527 — Current Eligibility Recomputation + U3K Input Plan v0.39

## Stage
- Mode: BOUNDED OFFLINE ELIGIBILITY DRY-RUN ONLY
- Start HEAD: `9d195dbbf89f11b51d28cc987c5ed4686965ca1e`
- Productive authority: Welt-Swing v7.2 only
- LONG DEV: DEV / RESEARCH / SHADOW
- Membership != Eligibility != Scan != Execution

## Inputs and closed authorities
- Research Partial: 2,527 current securities; membership unchanged.
- Company/Security Mapping v1: canonical `Security_Key = WSSEC:<Source_WS_ID>`.
- History QA v1 policy unchanged: >=260 unique / >=252 valid observations.
- Liquidity QA v1 policy unchanged: >=20m EUR preferred; 15–20m standard; 5–15m low exception; <5m fail; >=18/20 usable sessions.
- 522 market evidence: validated run 35905876433 / SHA 126dbcd14282af1ff2a72a67f99ffb8ae7e180a3; acquisition 521 READY / 1 SHORT_HISTORY.
- No Alpha Vantage, no market-provider acquisition, no live Scalable query.

## Dry-run result
- Prior authoritative Strict diagnostic: **759** (unchanged authority)
- Proposed current dry-run: **1425 PASS_STRICT_CANDIDATE**
- Overlap with prior 759: **622**
- Proposed additions: **803**
- Proposed removals: **137**
- Frozen U3K: **0**
- Universe write: **false**
- P0/P1/P2: **NOT RUN**

Eligibility distribution:
- FAIL_LIQUIDITY: 48
- HISTORY_CONFLICT: 236
- HISTORY_PARTIAL: 5
- HISTORY_UNAVAILABLE: 19
- INSTRUMENT_REVIEW: 667
- INSUFFICIENT_HISTORY: 7
- LOW_LIQUIDITY_EXCEPTION: 120
- PASS_STRICT_CANDIDATE: 1425

Proposed Strict by evidence cohort:
- BASE_1633: 622
- US1: 372
- US2: 368
- AU1: 63

All 137 removals from the prior 759 are current **HISTORY_CONFLICT** cases under closed History QA v1 evidence. No prior-759 row is removed because of a relaxed/tightened threshold.

## SOLS
`WSSEC:WS:XNAS:SOLS` / `WS:XNAS:SOLS` remains **INSUFFICIENT_HISTORY_FOR_STANDARD_U3K** with 231 ordinary valid observations. It remains in Research Partial, is excluded from proposed Strict, and does not block evaluation of the other 2,526 rows.

## CTD separation
`WSSEC:WS:XASX:CTD` is acquisition **READY** but has 247 ordinary traded observations after suspension rows are excluded from ordinary adjacency/history counting. Therefore it is also **INSUFFICIENT_HISTORY_FOR_STANDARD_U3K**. This demonstrates that acquisition READY is not automatic eligibility.

## U3K input plan
The plan contains exactly **1425 proposed eligible inputs**. Because 1425 < 3000, no cap is required. This is a plan only: `Freeze_Authorized=NO`, Frozen remains 0, and no membership artifact is populated.

## Validation
Focused offline validation: **20/20 PASS**. Deterministic generation was checked before persistence. No market-provider calls, no Universe write, no Frozen write, no P0/P1/P2 execution.
