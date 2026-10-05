# P0 Breakout Compression VCP HOLDOUT Execution — G-P0-10 v1.08

Status: **INVALIDATED / FAIL-CLOSED — HOLDOUT SINGLE-USE PROTOCOL BREACH**.

The earlier v1.08 PASS claim is superseded by corrective binding **G-P0-10-CORR / v1.09**. The frozen finalist remains **L1-C07-PIVOT_PROXIMITY_STRICT**, semantic SHA256 `7aabed14feb3ab902223f981619864b24aecc25b51c3d67f4026e4a8e357c201`. No parameter promotion or P0 authorization follows from any v1.08 HOLDOUT output.

The sealed HOLDOUT contract states that later use is **"exactly once only after LANE1_FINALIST_FROZEN=YES"**. G-P0-09/v1.07 independently binds the HOLDOUT as single-use.

## Corrected execution chronology

- Run **37236828268** failed during governed-input verification; the C07 execution step was skipped.
- Run **37236886982** reached the execution step but failed before scoring because pandas was unavailable.
- Run **37236942896** reached the execution step but failed before `execute_holdout(...)` was evaluated because `json` was undefined.
- Run **37237024056**, head `2e278d4539bde3ea3d1d71d240e4507f241cd29b`, is the **first actual HOLDOUT scoring execution**. Governed inputs passed. The executor entered `execute_holdout`, read the HOLDOUT-bounded market data, evaluated C07 status and forward outcome fields across the retained mask, constructed the dataframe, and then failed on the post-loop assertion `raw == 84925` with observed raw count 87,523. Failure occurred before row-level CSV persistence. GitHub artifact count for this run is zero.
- Run **37237147539**, head `1c9dfea9034a38ac237d7d3109db0b0e4adcc3f7`, subsequently succeeded. The only code delta from the first scoring run replaced the failing raw-count assertion with protocol-bound `raw_protocol=84925`; C07 scoring and forward-outcome logic did not change. This therefore constitutes a **second HOLDOUT scoring execution** without reuse authorization.

The successful second run produced 66,148 persisted rows and the technically intact payload `WELT-SWING_L1_BREAKOUT_VCP_HOLDOUT_v1.08_Payload.zip`, Drive ID `1dJImdpnpmjkNEqkRjxO6fn1ma0WUr6Oi`, SHA256 `d90ba32035ac62f09a710a0094b0905ee8ba4a7c51ac76049a4fe5565c1fbbc6`. Its ZIP, member hashes and row count are retained as forensic evidence, but the payload is **not authoritative HOLDOUT evidence** because it arose from unauthorized reuse.

Corrected state: HOLDOUT opened = YES; single-use consumed = YES; reuse authorized = NO; first-use row-level evidence persisted = NO; valid single-use HOLDOUT evidence available = NO; original HOLDOUT reusable = NO.

Parameters remain **FROZEN_FINALIST_NOT_PROMOTED**. The current P0 pointer remains **G-P0-01/v0.99** and P0 remains unauthorized.

Hard stop: **no further use of this HOLDOUT, no parameter promotion, no P0, no Lane 2**.

Next gate: **MANAGER GOVERNANCE — authorize a new independent HOLDOUT or leave the lane DEV_UNCONFIRMED**.
