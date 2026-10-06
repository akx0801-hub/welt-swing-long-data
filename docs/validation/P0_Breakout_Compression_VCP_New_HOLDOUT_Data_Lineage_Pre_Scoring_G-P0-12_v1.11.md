# P0 Breakout Compression VCP New HOLDOUT Data Lineage / Pre-Scoring — G-P0-12 v1.11

Status: **BLOCKED — PRE_SCORING_BLOCKED_MANAGER_REVIEW_REQUIRED**.

The G-P0-12 authority remains `NEW_INDEPENDENT_HOLDOUT_DATA_LINEAGE_AND_PRE_SCORING_AUTHORIZED_HOLDOUT_NOT_OPENED`. The authorized bounded data acquisition was performed, but the technical pre-scoring gate did not pass because 15 Frozen-1425 securities remain in the established price-cache QA state `QUARANTINE / SUSPICIOUS_RETURN_NEEDS_REPAIR`. No QA threshold was relaxed, no security was removed from the frozen universe, no alternative provider was substituted, and no second Yahoo acquisition was started.

## Bound data lineage

Required start HEAD: `b433af12667cb4843653b1d14127b59054adf7d4`.

Fresh period was prospectively frozen before fetch at **2026-09-04 through 2026-10-05**. Provider was exclusively **YFINANCE_FREE / yfinance==1.6.0**. The bounded acquisition used 16 provider calls; Alpha Vantage, EODHD, Scalable, TradingView, News and Fundamentals calls were zero.

The canonical v0.53 recovery source remains Drive file `1lrp_9V0KlWedKYoK7KBNa4zyVqBj1iPg`, archive SHA256 `f54f1520e6cfcefbca043bc782ccf71ddd0e70538722ee1c3857551396761e95`, SQLite SHA256 `bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc`. The original remained unchanged. The historical partition through 2026-09-03 matches exactly before/after and no fresh provider value was written into it.

The materialized v1.11 SQLite contains 692427 historical rows plus 28699 fresh rows, 721126 total. Earliest/latest dates are 2024-09-16 / 2026-10-05; rows after 2026-10-05 are zero. SQLite SHA256 is `245793920911e318ad8b16ad08e35321677a72e8006c64a597b725d92fd7c251`.

## Provider mapping and QA

Frozen universe mapping is 1425 mapped / 0 unmapped and was frozen before the first price call. No unexpected symbol identity change was accepted.

Final QA states are 1410 `READY` and 15 `QUARANTINE`. The 15 blockers are persisted in `pre_scoring_blockers_v1.11.csv`. Six suspicious-return flags are inherited from dates at or before 2026-09-03 in the immutable foundation; nine have a suspicious date after 2026-09-03, including the new boundary/data period. These are retained for Manager review rather than being normalized, ignored, remapped, or refetched.

## Candidate-independent anchor population

The deterministic population manifest contains 28699 post-boundary rows, of which 7288 satisfy the predeclared technical eligibility rule. Future information was used only to count whether 5/10/15 valid sessions exist. No future prices were transformed into outcome metrics.

## No HOLDOUT opening

C07 was not scored. HIT/FALSE was not computed. No `FWD_CLOSE_RETURN_h`, `FWD_MAX_PIVOT_EXTENSION_ATR_h`, `FWD_MAX_DRAWDOWN_ATR_h` or `FWD_ANY_CLOSE_ABOVE_ANCHOR_PIVOT_h` value was generated.

The HOLDOUT remains `SEALED_NOT_OPENED` with `HOLDOUT_OPENED=NO`, `HOLDOUT_SCORING_STARTED=NO`, and `HOLDOUT_SINGLE_USE_CONSUMED=NO`.

## Drive persistence

The exact acquisition package is preserved at Drive file `1UnfEKgQQiXbKXa1hiYD_Fn2liBVr2IqD`. ZIP SHA256 is `3c305545c3243616cfdf21597d0cbbda6755b5649211ee112d3c9d4a44400fb2`. Direct roundtrip verification passed with exact member set, ZIP integrity, SQLite SHA, schema, row count and date bounds.

## Governance result

This is **not** a successful pre-scoring PASS and does not authorize the single-use execution gate. P0 remains G-P0-01/v0.99 and unauthorized. Lane 2 remains unchanged and unauthorized.

Next state: **PRE_SCORING_BLOCKED_MANAGER_REVIEW_REQUIRED**.

Hard stop: **STOP_PRE_SCORING_BLOCKED_HOLDOUT_SEALED_NO_SCORING_NO_OUTCOMES_NO_PROMOTION_NO_P0_NO_LANE2**.
