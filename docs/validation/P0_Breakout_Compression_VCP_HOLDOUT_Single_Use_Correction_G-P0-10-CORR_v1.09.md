# Breakout Compression VCP HOLDOUT Single-Use Correction — G-P0-10-CORR v1.09

## Verdict

**FAIL-CLOSED — G-P0-10/v1.08 is invalidated as authoritative HOLDOUT evidence because the sealed single-use HOLDOUT was scored more than once.**

This correction preserves all historical commits and payloads. It does not rerun HOLDOUT, retune parameters, authorize promotion, authorize P0, or authorize Lane 2.

## Governing rule

The sealed protocol file `output_p0_breakout_compression_vcp_validation_protocol_v1_02/holdout_seal_contract_v1.02.json` binds later HOLDOUT use to **"exactly once only after LANE1_FINALIST_FROZEN=YES"**. G-P0-09/v1.07 separately states that the authorized HOLDOUT is single-use.

## Directly verified chronology

1. Run `37236828268`: failed at governed-input verification; C07 execution skipped.
2. Run `37236886982`: governed inputs passed; execution failed before scoring because pandas was not installed.
3. Run `37236942896`: dependencies and governed inputs passed; execution failed before `execute_holdout(...)` was evaluated because `json` was undefined.
4. Run `37237024056`, head `2e278d4539bde3ea3d1d71d240e4507f241cd29b`: first actual C07 HOLDOUT scoring execution. The function evaluated C07 status and forward outcomes across the retained mask and constructed the dataframe before failing at the post-loop assertion with `AssertionError: (87523, 'raw')`. No workflow artifact was produced and row-level evidence was not persisted.
5. Run `37237147539`, head `1c9dfea9034a38ac237d7d3109db0b0e4adcc3f7`: second C07 HOLDOUT scoring execution, successful. The code delta from run 4 changed only the raw-population assertion/binding and return field; scoring logic did not change. Reuse was not authorized.

Run 5 produced technically coherent persisted evidence: GitHub artifact `11316550633`, 5,061,518 bytes, SHA256 `d90ba32035ac62f09a710a0094b0905ee8ba4a7c51ac76049a4fe5565c1fbbc6`; Drive file ID `1dJImdpnpmjkNEqkRjxO6fn1ma0WUr6Oi` has the same byte count and SHA after direct round-trip verification. The ZIP contains exactly `holdout_anchor_evidence_v1.08.csv` and `holdout_payload_manifest_v1.08.json`; the CSV has 66,148 data rows. This is preserved as **non-authoritative forensic evidence from an unauthorized second scoring execution**.

## Corrected state

- HOLDOUT_OPENED = YES
- HOLDOUT_SINGLE_USE_CONSUMED = YES
- HOLDOUT_REUSE_AUTHORIZED = NO
- FIRST_USE_EVIDENCE_PERSISTED = NO
- VALID_SINGLE_USE_HOLDOUT_EVIDENCE_AVAILABLE = NO
- ORIGINAL_HOLDOUT_REUSABLE = NO
- PARAMETER_PROMOTION_AUTHORIZED = NO
- LANE1_AUTOMATED_CONTRACT_READY = NO
- P0_RUN_AUTHORIZED = NO
- Current P0 pointer remains G-P0-01/v0.99

## Hard stop

No further access to the original HOLDOUT is permitted. No parameter promotion, P0, or Lane 2 action is permitted from v1.08 evidence.

The next gate is a manager-governance decision to authorize a **new independent HOLDOUT** or leave this lane **DEV_UNCONFIRMED**.
