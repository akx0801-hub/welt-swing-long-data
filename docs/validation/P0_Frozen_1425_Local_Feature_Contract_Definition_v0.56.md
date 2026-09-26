# P0 Frozen-1425 Local Feature Contract Definition v0.56

## 1. Gate verdict
**PASS_ALL8_CONTRACTS_DEFINED**

All eight remaining v0.55 local-feature semantic gaps are now fully defined as contracts. This gate does not implement or materialize them. v0.57 implementation is authorized; P0_LOCAL_FEATURE_LAYER_READY remains NO.

## 2. Start HEAD
b6426f24c30c213949d436d205f9188f22c21d84

## 3. v0.55 authority validation
Workflow 36230843835; artifact 10902665790; artifact digest sha256:a6faf3156763a9ff4d6eba5322aa6e62c1f97a75797b09b910fba762917184a8; semantic materialization SHA 81f52fc0098c72d0836d014bf17975b8fcc729489a9eb67f146005be913ac2bc. Frozen=1425; Price Cache READY=1425; QUARANTINE=0; canonical numeric features=23; FEATURE_READY=0; FEATURE_PARTIAL=1425.

## 4. Remaining-8 reconciliation
All eight families from v0.55 end CONTRACT_DEFINED.

## 5-12. Defined contracts
EMA20_Slope_5 = EMA20[t]/EMA20[t-5 valid]-1. EMA50_Slope_10 = EMA50[t]/EMA50[t-10 valid]-1. Range family adds Range5_Pct, Range10_Pct, RangeCompression_5_20 and RangeCompression_10_20 while retaining Range20_Pct. RVOL20 uses current Volume_Tech over the median of the previous 20 valid observations, excluding current from baseline. Gap_Over_ATR14 uses signed Open[t]-Close[t-1 valid] over ATR14[t-1 valid]. DailyMove_Over_ATR14 uses signed Close[t]-Close[t-1 valid] over ATR14[t-1 valid]. RECENT_IMPULSE_DESCRIPTORS is a semantic composition of R5/R20/R60, DailyMove_Over_ATR14 and RVOL20 without an event threshold. Relevant-high distance adds Dist_High20 and Dist_High60 and retains Dist_High252.

## 13. Current-bar inclusion policy
Price-structure rolling windows include current valid t. Comparison baselines used to judge current activity exclude current t.

## 14. ATR reference policy
Existing descriptive ATR14 remains current-t. Current-event magnitude features use ATR14[t-1 valid].

## 15. Filtered-series policy
Every definition uses the v0.53/v0.55 canonical filtered valid technical series; previous means previous VALID observation and rolling N means N valid observations.

## 16. Null / zero-denominator policy
Undefined denominator or missing required input => canonical null and capability failure. No zero fill, infinity, epsilon or substitution.

## 17. Minimum history contract
EMA20_Slope_5=25; EMA50_Slope_10=60; Range5=5; Range10=10; compression ratios=20; RVOL20=21 plus volume completeness; Gap/ATR=15; DailyMove/ATR=15; Dist_High20=20; Dist_High60=60; recent-impulse composition=61 plus RVOL volume completeness. Existing full layer still has 252-observation requirements.

## 18. Final canonical names
EMA20_Slope_5; EMA50_Slope_10; Range5_Pct; Range10_Pct; RangeCompression_5_20; RangeCompression_10_20; RVOL20; Gap_Over_ATR14; DailyMove_Over_ATR14; Dist_High20; Dist_High60; semantic family RECENT_IMPULSE_DESCRIPTORS.

## 19. New numeric features expected
**11**

## 20-23. Decision counts
CONTRACT_DEFINED=8; CONTRACT_PARTIALLY_DEFINED=0; CONTRACT_DEFERRED=0; CONTRACT_REJECTED=0.

## 24. Remaining ambiguities
**None within the eight v0.56 contracts.** P0 decision thresholds remain intentionally undefined.

## 25. V0_57_LOCAL_FEATURE_IMPLEMENTATION_AUTHORIZED
**YES**

## 26. P0_LOCAL_FEATURE_LAYER_READY
**NO** — contract-only gate.

## 27. HOME_MARKET_RS_READY
**NO / unchanged**

## 28. SECTOR_RS_READY
**NO / unchanged**

## 29. Parameter authority
Unchanged: output_p0_lane_shadow_validation_v0_21/p0_lane_parameter_registry_v0.21.json; p0_numeric_pass_thresholds=[]; promoted_lane_pass_rules=[].

## 30. Feature materialization runs
**0**

## 31. P0 runs
**0**

## 32. Price runtime / Frozen immutability
Price Runtime remains bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc / 144539648 bytes and was not opened or written. Frozen remains 1425 members / 54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb.

## 33. Provider calls
Market provider=0; Yahoo/yfinance=0; EODHD=0; Alpha Vantage=0; Scalable=0.

## 34. Test / contract validation results
24/24 persisted contract-validation tests PASS plus focused pytest in the successful workflow. Earlier run 36235530681 failed on test-harness wording assertions before evidence generation; no contract artifact was uploaded.

## 35. Files
The bounded v0.56 contract package is persisted under output_p0_frozen_1425_local_feature_contract_v0_56/ and this report under docs/validation/. No feature matrix exists.

## 36. Commit
Final persistence commit is created by the bounded persistence workflow after artifact verification.

## 37. Next gate
**P0 FROZEN-1425 LOCAL FEATURE CONTRACT v0.56 BOUNDED IMPLEMENTATION / PROMOTION GATE v0.57**

Hard stop: no implementation, no materialization, no RS, no P0/P1/P2, no parameter promotion, no shortlist, no Universe mutation, no Scalable, no trading.
