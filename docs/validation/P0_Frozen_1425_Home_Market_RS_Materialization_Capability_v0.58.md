# P0 Frozen-1425 Home-Market RS Materialization / Capability v0.58

## Verdict
**PASS_HOME_MARKET_RS_READY**

## Start and input authority
- Required start HEAD: 80d80eee5e8a2e6ddad5f7b7b1231b9a3da21895
- v0.57 workflow/artifact: 36239952535 / 10905448132 / sha256:7f35e18264110c6a6a84205ab443a7b1c3cabcbaebdb3e6d6af79df6361e1c00
- v0.57 local feature semantic SHA: 177cff93408fe4c00c45ed4c9772f2a88321f6d8df43b6e67216c3f383834be9
- Frozen: 1425 / 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb
- Price Runtime: bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc / 144539648 bytes

## Contract binding
Master authority requires 20/60-day return difference versus home market and permits reproducible internal peer/market groups for early discovery. v0.20 defines a leave-one-out median per Primary_Universe_Index among synchronized peers; v0.21 preserves that reference and explicitly disclaims an official-index benchmark claim. v0.44 persists the current Frozen-1425 Primary_Universe_Index mapping. v0.58 binds synchronization per security to peers with the exact same feature_as_of_date, as required by the no-artificial-global-date rule. No new RS threshold or ranking semantic is introduced.

Canonical formulas:
- HomeMarket_RS20_Excess = R20 - leave-one-out median(R20 of same Primary_Universe_Index and exact same feature_as_of_date)
- HomeMarket_RS60_Excess = R60 - leave-one-out median(R60 of same Primary_Universe_Index and exact same feature_as_of_date)

Missing mapping, missing/non-finite return input, or fewer than one synchronized peer is fail-closed as RS_NOT_VERIFIED. No substitute benchmark, ETF fallback, MIC-to-country inference, zero fill, epsilon, or external benchmark acquisition is permitted.

## Benchmark mapping / cohort readiness
- AU_SP_ASX200: 63 Frozen rows; MICs XASX; 1 as-of date(s); same-date peer count range 62..62.
- BR_IBRX100: 37 Frozen rows; MICs BVMF; 1 as-of date(s); same-date peer count range 36..36.
- CN_CSI300: 294 Frozen rows; MICs XSHE|XSHG; 1 as-of date(s); same-date peer count range 293..293.
- IN_NIFTY50: 45 Frozen rows; MICs XNSE; 1 as-of date(s); same-date peer count range 44..44.
- JP_N225: 197 Frozen rows; MICs XTKS; 1 as-of date(s); same-date peer count range 196..196.
- TW_TW50: 49 Frozen rows; MICs XTAI; 1 as-of date(s); same-date peer count range 48..48.
- US_SP400: 368 Frozen rows; MICs XNAS|XNYS; 1 as-of date(s); same-date peer count range 367..367.
- US_SP500: 372 Frozen rows; MICs XNAS|XNYS; 1 as-of date(s); same-date peer count range 371..371.

## Materialization / capability
- Materialized: True
- HOME_MARKET_RS_READY: True
- Ready / Total: 1425 / 1425
- Semantic digest: 2fef5b0ce4d030008282f9421f818d42dae6bc8d39c20d21a336ce998622fd32
- Determinism match: True
- Input blockers: []

## Temporal integrity
Reference peers are exact same-date peers within the mapped Primary_Universe_Index cohort. Different exchange calendars therefore do not force a global date and cannot import later peer observations into an earlier security as-of. Cross-market temporal audit covers XNYS, XNAS, XASX, XTKS, XTAI, XSHG, XSHE, XNSE and BVMF.

## Immutability / governance
- Price Runtime unchanged: True
- Frozen unchanged: True
- v0.57 local features unchanged: True
- Sector RS: NOT RUN / READY remains NO
- Parameter authority unchanged: output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json
- p0_numeric_pass_thresholds=[]; promoted_lane_pass_rules=[]
- P0 runs=0; P1/P2 runs=0
- Provider calls: market=0, Yahoo/yfinance=0, EODHD=0, Alpha Vantage=0, Scalable=0

## Artifact authority
- Workflow run: 36242803316
- Workflow head: 964ba89cdf1ea764dd07b65d7f1e8010c09feb86
- Artifact: 10905869033
- Artifact name: p0-frozen-1425-home-market-rs-v0.58-36242803316
- Artifact digest: 54dc5168218c7a211c6a0d66fc236c1e95a7cfdabef2acadf79282c8f1b5ae1c

## Next gate
**P0 FROZEN-1425 SECTOR METADATA / SECTOR-RS AUTHORITY GATE**

Hard stop: no Sector RS, no P0/P1/P2, no parameter promotion, no shortlist, no Universe mutation, no Scalable, no trading.
