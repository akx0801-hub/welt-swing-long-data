# P0 Frozen-1425 Feature Materialization / Capability Gate v0.54

## Gate verdict
**PASS_WITH_LOCAL_FEATURE_MODEL_GAPS**

The current canonical-implemented technical subset materializes deterministically and completely for all 1425 Frozen securities, but the LONG DEV master specification requires additional local feature semantics that are not current canonical authority. P0_LOCAL_FEATURE_LAYER_READY remains NO.

## Start authority
Required start HEAD: 8106f8d7a348b4000b504da6b9a82d9fd1db1c33
Implementation HEAD: d81bc4d6741a0be557230f12920dd99d410803cd

## v0.53 authority validation
Run 36225840648; artifact 10900287789; runtime SHA bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc; bytes 144539648; integrity ok; price_daily 711204; states 1425; READY 1425; QUARANTINE 0.

## Canonical feature inventory
Current canonical-implemented authoritative subset: 21 features.
Close_Tech, EMA20, EMA50, SMA200, ATR14_Wilder_DEV, ATR14_Pct_DEV, R5, R20, R60, High20, High60, High252, Low20, Low60, Dist_EMA20, Dist_EMA50, Dist_SMA200, Dist_High252, Range20_Pct, MedianVolume20_Tech, MedianTurnover20_Native

Historical v0.19 augmented descriptors were inspected but not silently promoted. Home-market and sector RS are outside this gate.

Master-local blocking gaps:
- EMA20_SLOPE
- EMA50_SLOPE
- R1
- TRUE_RANGE_CURRENT
- RANGE_COMPRESSION_FAMILY
- RELATIVE_VOLUME_METRICS
- GAP_OVER_ATR
- DAILY_MOVE_IN_ATR
- RECENT_IMPULSE_DESCRIPTORS
- RUNUP_5_20_60_SEMANTICS
- RELEVANT_HIGH_DISTANCE_FAMILY

## Formula / implementation binding
All 21 materialized fields are bound to scripts/feature_builder.py at the validated repository blob. Formula evidence is persisted in feature_formula_binding_v0.54.csv. No formula, threshold or null default changed.

## Materialization scope
Rows: 1425. Semantic SHA-256: c5d9c6eabbbef10909b7a0df8b4bb8eb5ff32130d8c85162f5f2f4e4a7a4bed6. Valid-bar range: 293 to 508. Excluded source-defect bars: 8. Market-data downloads: 0.

## Capability counts
FEATURE_READY=0; FEATURE_PARTIAL=1425; FEATURE_BLOCKED_INSUFFICIENT_HISTORY=0; FEATURE_BLOCKED_INPUT=0; FEATURE_COMPUTATION_ERROR=0; NOT_VERIFIED=0.
The entire Frozen-1425 population is the exact non-ready set, for the common model-level reason MASTER_REQUIRED_LOCAL_FEATURE_MODEL_NOT_FULLY_CANONICAL_IMPLEMENTED.

## Null / non-finite audit
All 21 current canonical-implemented feature columns are finite for all 1425 securities. NULL/NaN=0; +Inf=0; -Inf=0.

## History sufficiency
Minimum filtered valid observations: 293. Longest current canonical finite-window requirement: 252. History QA v1 unchanged.

## ASX-8 regression
All eight v0.53 source-defect securities pass. The raw 2024-11-15 bar remains stored, the complete invalid bar is excluded from technical input, and EMA20/EMA50/ATR14 match independent filtered-series recomputation exactly.

## Recursive reproducibility
EMA20 exact 1425/1425; EMA50 exact 1425/1425; ATR14 exact 1425/1425. Semantics: DETERMINISTICALLY_COMPUTED_FROM_FILTERED_VALID_SERIES.

## Temporal integrity
All 1425 pass; feature_as_of_date equals each security's latest eligible valid bar; no row after own as-of is consumed.
As-of distribution: {"2026-09-21": 368, "2026-09-22": 63, "2026-09-24": 994}

## Determinism
Pass-1 semantic digest = pass-2 semantic digest = c5d9c6eabbbef10909b7a0df8b4bb8eb5ff32130d8c85162f5f2f4e4a7a4bed6. PASS.

## Source-defect provenance
Eight source-defect securities and eight excluded bars retain dates and filtered-policy provenance in the feature outputs.

## Price runtime immutability
Input SQLite SHA and bytes unchanged; price_daily digest unchanged; provider mapping digest unchanged; cache state remains 1425 READY / 0 QUARANTINE.

## Frozen / mapping reconciliation
Frozen members 1425; SHA-256 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb; identities and mappings unchanged.

## RS and parameter authority
HOME_MARKET_RS_READY=NO unchanged. SECTOR_RS_READY=NO unchanged. No RS materialization. Parameter authority remains output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json, with no numeric P0 thresholds and no promoted lane rules.

## P0 / provider calls
P0 runs=0. Market provider=0; Yahoo/yfinance=0; EODHD=0; Alpha Vantage=0; Scalable=0.

## P0_LOCAL_FEATURE_LAYER_READY
**NO**. The 21-field current canonical subset is data-complete, but the master-required local feature contract is not fully canonicalized/implemented.

## Tests
39/39 PASS plus focused pytest.

## Artifact authority
Workflow run 36228518000; feature artifact 10901437101; artifact digest sha256:0c6eec3a41a26940b4e1325532f2e7bf240f1d362f147f4b52a3943f6f5dfe47; semantic feature digest c5d9c6eabbbef10909b7a0df8b4bb8eb5ff32130d8c85162f5f2f4e4a7a4bed6. No separate feature-runtime database was created.

## Next gate
**P0 FROZEN-1425 MASTER-REQUIRED LOCAL FEATURE IMPLEMENTATION / PROMOTION REMEDIATION GATE**

Hard stop: no P0 classification, no P1/P2, no Home-Market RS, no Sector RS, no parameter promotion, no shortlist, no Universe mutation, no Scalable, no trading.
