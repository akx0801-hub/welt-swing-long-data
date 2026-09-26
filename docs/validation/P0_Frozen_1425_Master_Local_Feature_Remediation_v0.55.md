# P0 Frozen-1425 Master-Required Local Feature Remediation v0.55

## 1. Gate verdict
**PASS_WITH_REMAINING_CONTRACT_GAPS**

Three of the eleven v0.54 master-local contract gaps are derivable from existing authority and are promoted in v0.55. Eight remain contract-ambiguous and are deliberately not implemented. P0_LOCAL_FEATURE_LAYER_READY remains NO.

## 2. Start HEAD
4fd2d914b2bbb0fcf2b347890f8d652ee80c4f00

## 3. v0.54 authority validation
Workflow 36228518000; artifact 10901437101; artifact digest sha256:0c6eec3a41a26940b4e1325532f2e7bf240f1d362f147f4b52a3943f6f5dfe47; semantic feature SHA-256 c5d9c6eabbbef10909b7a0df8b4bb8eb5ff32130d8c85162f5f2f4e4a7a4bed6. Frozen=1425; Price Cache READY=1425; QUARANTINE=0; FEATURE_READY=0; FEATURE_PARTIAL=1425.

## 4. Master gap reconciliation
All eleven v0.54 gaps were reconciled exactly. Resolved: R1, TRUE_RANGE_CURRENT, RUNUP_5_20_60_SEMANTICS. Remaining: EMA20_SLOPE, EMA50_SLOPE, RANGE_COMPRESSION_FAMILY, RELATIVE_VOLUME_METRICS, GAP_OVER_ATR, DAILY_MOVE_IN_ATR, RECENT_IMPULSE_DESCRIPTORS, RELEVANT_HIGH_DISTANCE_FAMILY.

## 5. Contract binding — all 11
- EMA20_SLOPE: **CONTRACT_AMBIGUOUS** — Master requires a slope but does not bind horizon or normalization; v0.19 5-session percentage formula is historical evidence only; v0.21 validates sign only.
- EMA50_SLOPE: **CONTRACT_AMBIGUOUS** — Master does not bind 10-session percentage slope; historical v0.19 cannot promote it by itself.
- R1: **CONTRACT_DERIVABLE** — Master explicitly places R1 in the same Rn family as canonical R5/R20/R60; unique extension of the already-canonical n-return primitive is n=1.
- TRUE_RANGE_CURRENT: **CONTRACT_DERIVABLE** — Canonical ATR14 already computes the exact TR primitive; Master separately requires True Range, so exposing the current value reuses the existing single source of truth.
- RANGE_COMPRESSION_FAMILY: **CONTRACT_AMBIGUOUS** — Current shadow relation does not uniquely bind a canonical feature set or normalization.
- RELATIVE_VOLUME_METRICS: **CONTRACT_AMBIGUOUS** — Master names RVOL concept but does not define mean/median, lookback, or current inclusion; v0.19 is historical evidence only.
- GAP_OVER_ATR: **CONTRACT_AMBIGUOUS** — Master does not specify gap numerator or ATR denominator timing; same-bar denominator leakage cannot be guessed.
- DAILY_MOVE_IN_ATR: **CONTRACT_AMBIGUOUS** — Feature name alone does not identify numerator or ATR reference point.
- RECENT_IMPULSE_DESCRIPTORS: **CONTRACT_AMBIGUOUS** — Master specifies the concept, not the impulse identification formula, lookback, directionality, or post-impulse window.
- RUNUP_5_20_60_SEMANTICS: **CONTRACT_DERIVABLE** — The Run-up classification explicitly requires 5/20/60-day performance; this uniquely maps to already-canonical R5/R20/R60 without duplicate aliases.
- RELEVANT_HIGH_DISTANCE_FAMILY: **CONTRACT_AMBIGUOUS** — Repository evidence contains more than one plausible high-distance normalization/window; Master does not choose among them.

## 6-10. Contract counts
CONTRACT_EXACT=0; CONTRACT_DERIVABLE=3; CONTRACT_AMBIGUOUS=8; CONTRACT_CONFLICT=0; CONTRACT_NOT_FOUND=0.

## 11. Implemented / promoted features
- R1 — new canonical feature column: one-valid-observation split-normalized close-to-close decimal return.
- TrueRange_Current — new canonical feature column exposing the existing canonical ATR true-range primitive.
- RUNUP_5_20_60_SEMANTICS — canonical semantic binding to existing R5/R20/R60; no duplicate alias columns.

## 12. Features not implemented and why
EMA20_SLOPE and EMA50_SLOPE: horizon/normalization not fixed by Master. RANGE_COMPRESSION_FAMILY: exact member set/normalization not fixed. RELATIVE_VOLUME_METRICS: numerator/baseline/window not fixed. GAP_OVER_ATR: gap and ATR timing not fixed. DAILY_MOVE_IN_ATR: numerator/sign/ATR timing not fixed. RECENT_IMPULSE_DESCRIPTORS: identification/lookback/direction/post-window not fixed. RELEVANT_HIGH_DISTANCE_FAMILY: high selection and percent-vs-ATR normalization not fixed.

## 13. Canonical feature registry
v0.55 registry retains the existing 21 entries, adds R1 and TrueRange_Current as CANONICAL_IMPLEMENTED_PROMOTED, and adds the Run-up semantic-family binding. Registry file: canonical_feature_registry_v0.55.csv.

## 14. Full Frozen materialization
1425/1425 rows materialized. Canonical numeric columns: 23. Semantic SHA-256: 81f52fc0098c72d0836d014bf17975b8fcc729489a9eb67f146005be913ac2bc. Source-defect securities=8; excluded bars=8.

## 15. Existing-21 regression
PASS. The complete old-21 canonical semantic digest remains exactly c5d9c6eabbbef10909b7a0df8b4bb8eb5ff32130d8c85162f5f2f4e4a7a4bed6. No existing canonical formula changed.

## 16. ASX-8 regression
8/8 PASS. The raw 2024-11-15 bars remain stored and excluded from all technical input; R1 and TrueRange_Current independently match the filtered-series computation; R5/R20/R60 remain finite and filtered.

## 17. Temporal integrity
1425/1425 PASS; no future observation and no row after each security's feature_as_of_date.

## 18. Null / non-finite audit
All 23 canonical feature columns: NULL/NaN=0, +Inf=0, -Inf=0 across Frozen-1425. R1 division-by-zero behavior is fail-closed to None; production filtered prices are positive.

## 19. Determinism
Two full passes match exactly at 81f52fc0098c72d0836d014bf17975b8fcc729489a9eb67f146005be913ac2bc.

## 20. Remaining Master local gaps
EMA20_SLOPE, EMA50_SLOPE, RANGE_COMPRESSION_FAMILY, RELATIVE_VOLUME_METRICS, GAP_OVER_ATR, DAILY_MOVE_IN_ATR, RECENT_IMPULSE_DESCRIPTORS, RELEVANT_HIGH_DISTANCE_FAMILY.

## 21. Capability counts
FEATURE_READY=0; FEATURE_PARTIAL=1425; all other capability states=0. This remains a global contract blocker, not individual security-data failure.

## 22. P0_LOCAL_FEATURE_LAYER_READY
**NO**

## 23. HOME_MARKET_RS_READY
**NO / unchanged**

## 24. SECTOR_RS_READY
**NO / unchanged**

## 25. Parameter authority
Unchanged: output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json; p0_numeric_pass_thresholds=[]; promoted_lane_pass_rules=[].

## 26. P0 runs
**0**

## 27. Price runtime / Frozen immutability
Runtime SHA-256 unchanged at bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc; Frozen SHA-256 unchanged at 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb; provider mappings and raw OHLCV unchanged.

## 28-30. Provider calls
Market provider=0; Yahoo/yfinance=0; EODHD=0; Alpha Vantage=0; Scalable=0.

## 31. Test results
23/23 persisted gate tests PASS plus 6/6 focused pytest tests in the successful workflow.

## 32. Files
The bounded v0.55 evidence package is persisted under output_p0_frozen_1425_local_feature_remediation_v0_55/ and this report under docs/validation/.

## 33. Artifact / runtime authority
Successful workflow run 36230843835; artifact 10902665790; artifact digest sha256:a6faf3156763a9ff4d6eba5322aa6e62c1f97a75797b09b910fba762917184a8; feature semantic digest 81f52fc0098c72d0836d014bf17975b8fcc729489a9eb67f146005be913ac2bc. No separate feature-runtime database was created.

## 34. Commit
Final persistence commit is created by the bounded persistence workflow after artifact verification.

## 35. Next gate
**P0 FROZEN-1425 LOCAL FEATURE CONTRACT DEFINITION GATE — EMA SLOPES / RANGE-COMPRESSION / RELATIVE VOLUME / GAP-ATR / DAILY-MOVE-ATR / RECENT IMPULSE / RELEVANT-HIGH DISTANCE**

Hard stop: no Home-Market RS, no Sector RS, no P0 classification, no P1/P2, no parameter promotion, no shortlist, no Universe mutation, no Scalable, no trading.
