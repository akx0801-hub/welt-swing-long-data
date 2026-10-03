# P0 Breakout Compression VCP Architecture — G-P0-03 v1.01

Status: **PASS — APPROVED_ARCHITECTURE_PENDING_PARAMETER_VALIDATION**.

G-P0-03 binds Lane 1 to **CLASS_C_HISTORY_DERIVED_WITH_VALIDATED_PARAMETERS**. It is subordinate to the unchanged current P0 parameter authority G-P0-01/v0.99 and does not authorize P0.

The eight G-P0-02 decisions are resolved at architecture level: causal multi-week base; relational Stage-2 minimum `Close_Tech>SMA200 AND EMA50>SMA200 AND EMA50_Slope_10>0`; strict nested range compression; prior-exclusive 20-valid-bar coarse P0 pivot; ATR-normalized pivot-distance metric; parameterized causal climax composite; parameterized multi-horizon run-up extension; and the bound structural composition.

Shadow feasibility only: Trend_Context = 388 true / 1037 false / 0 null; strict compression = 1177 / 248 / 0; PriorHigh20_excl_t, pivot-distance and signed pivot-extension each finite 1425/1425; Close_Location_Value finite 1424/1425, with zero-range/undefined input remaining NOT_VERIFIED. No cutoff was tested.

The new primitives PriorHigh20_excl_t, P0_Pivot_Distance_ATR, Pivot_Extension_ATR and Close_Location_Value are contract definitions only and are not appended to G-FHR-01/v0.93. Missing/nonfinite/undefined required inputs map to `LANE1_NOT_VERIFIED_INPUT`; no fallback, imputation or current-High20 substitution is allowed.

Ten parameter families remain `UNBOUND_PENDING_VALIDATION`. Future validation must be historical, causal, time-separated, frozen before evaluation, free of look-ahead/current-snapshot percentile promotion, declare candidates before evaluation scoring, and report sensitivity/stability. Zero-hit and high-hit outcomes remain admissible.

No numeric cutoff, Lane PASS, security selection, P0/P1/P2 run, shortlist or Lane-2 work occurred. Next gate: **BREAKOUT_COMPRESSION_VCP PARAMETER VALIDATION PROTOCOL**.
