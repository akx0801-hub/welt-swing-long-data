# P0 Breakout Compression VCP New Independent HOLDOUT Protocol — G-P0-11 v1.10

Status: **PASS — NEW_INDEPENDENT_HOLDOUT_PROTOCOL_AUTHORIZED_EXECUTION_NOT_STARTED**.

## Governance basis

G-P0-10-CORR/v1.09 remains binding for the failed historical HOLDOUT sequence. G-P0-10/v1.08 remains **SUPERSEDED_FAIL_CLOSED** with decision **INVALIDATED_HOLDOUT_SINGLE_USE_PROTOCOL_BREACH**. The historical HOLDOUT is consumed, non-authoritative for promotion, and not reusable.

This v1.10 gate does not reopen or inspect the historical HOLDOUT payload. It does not use invalidated v1.08 HIT/FALSE counts or forward outcomes for any design choice, expectation, threshold, sample-size rule, power target, performance gate, or candidate selection.

## Frozen finalist

The only finalist that a later independent HOLDOUT may evaluate is the already frozen **L1-C07-PIVOT_PROXIMITY_STRICT**.

- Finalist semantic SHA256: `7aabed14feb3ab902223f981619864b24aecc25b51c3d67f4026e4a8e357c201`
- Candidate set: `L1_BREAKOUT_VCP_CSET_01`
- Candidate-set semantic SHA256: `8148c0bd2294bece39908d84394dda4fb0835210e83822997df12b9fbd0d6235`
- Contract source: `output_p0_breakout_compression_vcp_finalist_freeze_v1_07/finalist_contract_v1.07.json`
- `Pivot_Proximity_Cutoff_ATR = 0.75`

The finalist contract is immutable in this gate. Retuning and candidate reselection are prohibited.

## Why a new independent HOLDOUT is required

The maximum market day used by prior DESIGN, VALIDATION and historical HOLDOUT work is **2026-09-03**. The new HOLDOUT must therefore be temporally disjoint. Every future new-HOLDOUT anchor must satisfy:

`Anchor_Date > 2026-09-03`

No DESIGN, VALIDATION or historical-HOLDOUT anchor row may recur. Old anchor rows and the historical HOLDOUT payload may not be reused.

## Prospective window rule

v1.10 deliberately does **not** invent a fixed calendar end date.

Before any new market-data fetch and before any scoring, the next Manager gate must prospectively bind one new-data-lineage acquisition cutoff. That cutoff may not be selected from observed prices, C07 hit rates, returns, pivot extension, drawdown, candidate outcomes, or trial windows.

Once that future cutoff is frozen, the inclusion rule is mechanical and exhaustive:

> Include every `WS_ID × Anchor_Date` row from Frozen-1425 for which `Anchor_Date > 2026-09-03`, the anchor bar is technically valid, at least 252 valid technical observations exist through `t`, every required non-parameter Lane-1 input is finite, and at least 15 subsequent valid technical observations exist within the prospectively frozen new-data lineage snapshot.

For each WS_ID, the last eligible anchor is therefore the last anchor in that frozen snapshot with a complete `t+1..t+15` valid-session window. Partial or censored forward windows are prohibited. The valid-session and market-calendar semantics remain those of the frozen v1.02 protocol unless a later explicit Manager decision authorizes a technically necessary deviation.

## Frozen diagnostic contract

A later authorized execution may use only the existing structural diagnostics at 5, 10 and 15 valid sessions:

- `FWD_CLOSE_RETURN_h`
- `FWD_MAX_PIVOT_EXTENSION_ATR_h`
- `FWD_MAX_DRAWDOWN_ATR_h`
- `FWD_ANY_CLOSE_ABOVE_ANCHOR_PIVOT_h`

The anchor pivot remains frozen at `t`. There is no trade simulation, stop, target, CRV, scalar objective, or post-hoc performance gate.

Three-valued logic remains mandatory: `TRUE`, `FALSE`, `NOT_VERIFIED_INPUT`. Missing, nonfinite or undefined required inputs may not be imputed or silently replaced.

## Hardened single-use state machine

The new HOLDOUT begins as **SEALED_NOT_OPENED**:

- `HOLDOUT_OPENED = NO`
- `HOLDOUT_SCORING_STARTED = NO`
- `HOLDOUT_SINGLE_USE_CONSUMED = NO`

Consumption occurs at the **first actual access that scores C07 against the new HOLDOUT population or generates forward outcomes**. At that instant, regardless of later success or failure:

- `HOLDOUT_OPENED = YES`
- `HOLDOUT_SCORING_STARTED = YES`
- `HOLDOUT_SINGLE_USE_CONSUMED = YES`
- `HOLDOUT_REEXECUTION_AUTHORIZED = NO`

Successful persistence is not a condition of consumption. An assert, upload, workflow, persistence or packaging failure after opening never authorizes a second scoring run. There is no automatic or manual retry. A second scoring attempt without first defining another independent HOLDOUT is a protocol breach and requires Manager review.

## Pre-scoring validation

All technically testable bindings must be validated while the new HOLDOUT is still **SEALED_NOT_OPENED**. The pre-scoring gate must cover date-window binding, population-construction code, raw-count derivation, purge logic, market-calendar logic, required-history availability, full 15-session forward-window determination, Frozen-1425 binding, finalist contract, candidate-set SHA, code integrity, schema, Drive destination readiness, packaging logic and row conservation.

Those tests may not score C07 or generate forward outcomes. A failure before scoring leaves the HOLDOUT sealed and may be repaired and pre-validated again without consuming single use.

## Data lineage and provider boundary

The historical v0.53 cache remains read-only with SHA256 `bccca4f168eb5fbd68822d5ebd96419066c69400014b8525a0bec60df0b07afc`. It may not be mutated or append-extended.

Fresh post-2026-09-03 market data must later live in a new explicit lineage. v1.10 specifies that requirement but does not create the lineage and authorizes no data fetch.

Frozen Universe remains `universe/SWING_U3K_FROZEN_v0.5.csv`, 1,425 rows, SHA256 `54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb`. Membership is unchanged.

For this gate:

- `PROVIDER_CALLS_AUTHORIZED = NO`
- `PROVIDER_CALLS = 0`
- `NEW_MARKET_DATA_FETCH_AUTHORIZED = NO`
- Alpha Vantage remains prohibited.

## P0 and downstream state

The explicit current P0 pointer remains **G-P0-01/v0.99**:

- `P0_RUN_AUTHORIZED = NO`
- `AUTOMATED_P0_READY = NO`
- `p0_numeric_pass_thresholds = []`
- `promoted_lane_pass_rules = []`

No Lane-1 parameter promotion occurs. Lane 1 automated contract remains not ready. Lane 2 remains blocked and is not started.

## Next Manager gate

**BREAKOUT_COMPRESSION_VCP NEW INDEPENDENT HOLDOUT DATA-LINEAGE / PRE-SCORING AUTHORIZATION**

No next step is automatically authorized.
