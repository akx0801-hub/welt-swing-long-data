# P0 Breakout Compression VCP HOLDOUT Execution — G-P0-10 v1.08

Status: **PASS — HOLDOUT_EVIDENCE_COMPLETE_NO_PARAMETER_PROMOTION**.

The single frozen finalist **L1-C07-PIVOT_PROXIMITY_STRICT** was evaluated once on the sealed HOLDOUT under the v0.53 read-only price-cache lineage. Finalist semantic SHA256 is `7aabed14feb3ab902223f981619864b24aecc25b51c3d67f4026e4a8e357c201`. No comparator candidate was evaluated.

Population binding: raw eligible anchors 84,925; protocol purge 18,777; scored base 66,148. The market-data firewall was 2026-09-03; no later market bar was loaded. Full 15-valid-session forward windows remain inside HOLDOUT.

Execution counts: **4,290 HIT / 61,717 FALSE / 141 NOT_VERIFIED_INPUT**, conserving all 66,148 anchors. Hit share of evaluable anchors is 0.0649931067917039.

HIT structural diagnostics, median pivot extension ATR: 5d **0.7686045748**, 10d **1.2055215295**, 15d **1.5283513581**. HIT future-close-above-anchor-pivot shares: 5d **0.6351981352**, 10d **0.7459207459**, 15d **0.7981351981**. These are structural validation diagnostics only; no performance pass/fail decision is made here.

Primary_MIC and month stability evidence is persisted without reweighting. No trade simulation, scalar objective, expected hit-rate gate, comparator delta, retuning, or parameter promotion was performed.

The immutable row-level payload was uploaded to Drive as `WELT-SWING_L1_BREAKOUT_VCP_HOLDOUT_v1.08_Payload.zip`, Drive ID `1dJImdpnpmjkNEqkRjxO6fn1ma0WUr6Oi`, SHA256 `d90ba32035ac62f09a710a0094b0905ee8ba4a7c51ac76049a4fe5565c1fbbc6`. Drive round-trip verified exact bytes, ZIP integrity, exact two-member set, member hashes, 66,148 rows, candidate-set SHA, and finalist SHA.

HOLDOUT is now opened and single-use consumed. Reuse is unauthorized. Any post-HOLDOUT contract change requires a new HOLDOUT or remains DEV_UNCONFIRMED.

Parameters remain **FROZEN_FINALIST_NOT_PROMOTED**. Current P0 pointer remains G-P0-01/v0.99; P0 remains unauthorized.

Next Manager gate: **BREAKOUT_COMPRESSION_VCP HOLDOUT EVIDENCE REVIEW / PARAMETER PROMOTION DECISION**.
