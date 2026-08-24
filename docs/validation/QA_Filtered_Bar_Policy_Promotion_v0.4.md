# Welt-Swing Long DEV — Filtered Invalid-Bar QA Policy Promotion v0.4

## Decision

The previously shadow-tested invalid-bar rule is promoted into the core
`price_cache.py` QA logic.

This is a **data-quality policy promotion only**. It does not promote P0,
strategy parameters, production trading or any P1–P5 stage.

## Promoted rule

A cached daily series may remain eligible after technical filtering when all
conditions are met:

- no more than **2 invalid OHLC/volume bars**;
- invalid bars are no more than **1%** of the raw series;
- at least **260 valid bars** remain;
- the series is not stale;
- there are **zero suspicious >50% returns** after invalid bars are excluded.

Raw malformed bars remain in `price_daily` for audit. They are not rewritten,
imputed or deleted.

The existing feature builder already excludes invalid bars before EMA, SMA,
ATR, returns, highs/lows and turnover calculations.

## Override hierarchy

The promotion deliberately preserves stricter higher-priority checks.

1. More than two invalid bars or >1% invalid share:
   `QUARANTINE / INVALID_OHLC_OR_VOLUME`
2. Suspicious return after filtered-bar eligibility:
   `QUARANTINE / SUSPICIOUS_RETURN_NEEDS_REPAIR`
3. Stale last valid bar:
   `STALE / LAST_BAR_TOO_OLD`
4. Otherwise a qualifying 2-invalid-bar series:
   `READY / FILTERED_INVALID_BARS_EXCLUDED`

This keeps AB InBev, Sanlam and Vodacom quarantined because their two malformed
bars overlap with separate provider-scale anomalies.

## Validation basis

The preceding shadow remediation identified 23 two-invalid-bar candidates:

- 20 passed the strict shadow rule;
- 3 had overlapping suspicious-return anomalies and stayed quarantined.

The promotion workflow replays the rule against the complete post-targeted
SQLite cache. It performs **no price download**.

Expected active operational state after promotion:

- active universe: **3,657**
- READY before policy promotion: **3,582**
- exact new filtered-bar promotions: **20**
- READY after promotion: **3,602**
- QUARANTINE: **34**
- WARMUP: **20**
- STALE: **1**
- residual non-READY: **55**
- active feature rows: **3,602**

Coverage after promotion:

**3,602 / 3,657 = 98.4960% READY**

## Operational cache-state alignment

The remediated universe contains 3,657 active securities and six historical
rows that are now delisted/retired/inactive.

The workflow removes only those six rows from `cache_state`, so future coverage
and feature runs use exactly the active universe denominator.

Their historical `price_daily` rows remain in SQLite for audit. No historical
price row is deleted by the policy-promotion workflow.

## Transaction safety

The workflow does not edit the GitHub branch or main cache until all validation
gates pass.

1. It verifies the exact pre-promotion `price_cache.py` Git blob.
2. It patches the core only inside the Actions checkout.
3. It runs synthetic policy tests.
4. It restores the validated post-targeted cache.
5. It copies that cache to a work cache.
6. It requalifies all 3,657 active securities locally.
7. It requires the exact expected 20 promotions and exact final status counts.
8. Only after all gates pass does it:
   - promote the work cache to main;
   - save the new cache;
   - commit the patched `scripts/price_cache.py` and audit outputs.

A failed validation run therefore does not commit the core QA change.

## Outputs

- `output_qa_policy_promotion_v0_4/summary_v0.4.json`
- `output_qa_policy_promotion_v0_4/active_state_before_v0.4.csv`
- `output_qa_policy_promotion_v0_4/inactive_states_removed_v0.4.csv`
- `output_qa_policy_promotion_v0_4/active_state_after_v0.4.csv`
- `output_qa_policy_promotion_v0_4/state_changes_v0.4.csv`
- `output_qa_policy_promotion_v0_4/qa_filtered_promotions_v0.4.csv`
- `output_qa_policy_promotion_v0_4/residual_non_ready_v0.4.csv`
- `output_qa_policy_promotion_v0_4/features_active_v0.4.csv`
- `output_qa_policy_promotion_v0_4/promotion_status.txt`

## Governance

- yfinance/Yahoo remains the free price-data layer.
- No Alpha Vantage.
- No paid provider.
- No price/history download in this promotion.
- No automatic normalization of suspicious scale events.
- No P0.
- No P1–P5.
- No productive trading authority.

After a successful promotion, the data layer can proceed with 3,602 READY
securities while the remaining 55 non-READY rows stay explicit and auditable.
