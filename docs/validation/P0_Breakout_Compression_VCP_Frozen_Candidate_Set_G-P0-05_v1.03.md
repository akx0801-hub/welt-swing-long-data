# P0 Breakout Compression VCP Frozen Candidate Set — G-P0-05 v1.03

Status: **PASS — APPROVED_FROZEN_CANDIDATE_SET_NO_SCORING**.

Candidate set `L1_BREAKOUT_VCP_CSET_01` contains exactly 21 complete contracts: one reference and twenty one-parameter-at-a-time sensitivity variants. Semantic SHA-256: `8148c0bd2294bece39908d84394dda4fb0835210e83822997df12b9fbd0d6235`.

All numeric values are **NEW_G_P0_05_MANAGER_DEV_CANDIDATE_VALUES**. They were not inferred from Frozen distributions or DESIGN/VALIDATION/HOLDOUT outcomes and are not promoted P0 thresholds.

The base detector uses t-N..t-1 only, excludes anchor t, requires width <= boundary, every base-window close above contemporaneous SMA200, and exact Base_High_N == PriorHigh20_excl_t. Stage-2 persistence uses the bound relational context for K consecutive valid observations ending at t.

CLIMAX is an exact three-way AND classifier. EXCESSIVE_RUNUP is exactly (R20 AND R60) OR Pivot_Extension_ATR. Missing required inputs fail to LANE1_NOT_VERIFIED_INPUT with no fallback.

No Cartesian grid, random generation, optimization, outcome calculation, hit counts, selection rates, distributions, or rankings were performed. DESIGN scoring is authorized for the next separate stage but has not started. VALIDATION remains unauthorized; HOLDOUT remains sealed.

The current P0 pointer remains G-P0-01/v0.99 with empty numeric thresholds and promoted lane rules. P0/P1/P2 runs remain zero. Next gate: **BREAKOUT_COMPRESSION_VCP DESIGN EXECUTION**.
