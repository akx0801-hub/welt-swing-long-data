# WELT-SWING LONG DEV — CURRENT HANDOFF

**Updated:** 2026-08-24 22:46 CEST  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE

## Authority

Authoritative DEV master specification: `docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`.

Welt-Swing v7.2 remains unchanged and is the sole productive Swing authority until an explicit validated promotion. This handoff does not alter productive trade rules.

## Latest completed checkpoint — v0.18

Current main after the GitHub-Actions v0.18 output commit:

`9aa3c51f157708c63e07827912435478f42e21d0` — `Fix P0 research-partial integrity accounting v0.18`

Verified v0.18:

- schema: `WELT_SWING_P0_RESEARCH_PARTIAL_INTEGRITY_FIX_V0_18`;
- run status: `P0_RESEARCH_PARTIAL_INTEGRITY_FIX_V0_18_COMPLETE`;
- frozen research-partial rows: **2,037**;
- v0.17 historically reported feature matches: 2,037;
- actual feature-row matches after merge-indicator correction: **2,035**;
- valid AsOf rows: **2,035**;
- complete core feature rows: **2,035**;
- persistent feature usable rows: **2,035**;
- quarantine rows: **2**;
- quarantine reason: `UNMATCHED_FEATURE_ROW` for both;
- P0 survivors: 0;
- P0 run: false;
- validated automated P0 run: false;
- automated P0 ready: false;
- strict U3K frozen: false;
- full-scan claim: false;
- productive authority: false;
- Alpha Vantage: false;
- v0.17 history mutated: false.

The two real v0.18 quarantine identities are:

1. Anglo American — `WS:SRC:ZA_TOP40:C46C9A1E2438665A` — XJSE / ZAR;
2. Sasol — `WS:SRC:ZA_TOP40:3CA42D3A25639D8E` — XJSE / ZAR.

v0.18 corrected accounting only. It did not retroactively fabricate feature rows for these securities.

## Current research-partial coverage

The authoritative partial snapshot remains v0.16 with **2,037 Included Verified Strict** securities. This is not a frozen full U3K and cannot support a `weltweit bester Kandidat` claim.

Allowed later wording remains:

`bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage`.

## Next implementation checkpoint — v0.19

**`P0_FEATURE_AUGMENTATION_AND_PARAMETER_VALIDATION`**

v0.19 is prepared as a bounded feature-augmentation run over all 2,037 research-partial identities.

Key controls:

- yfinance/Yahoo only; Alpha Vantage prohibited;
- audited `price_cache.py` batch primitive;
- fixed daily-bar request window `2025-05-01` to end-exclusive `2026-08-24`;
- closed-bar reference `2026-08-21`, excluding the 2026-08-24 session;
- batch size 100, at most one identical retry and one regrouped rescue wave;
- no per-security symbol-search/web-lookup architecture;
- no FX, news, fundamentals, Scalable execution or sizing;
- runtime SQLite cache is not committed;
- no P0 PASS/FAIL lane decisions and no P0 survivors;
- no invented numeric P0 PASS thresholds;
- home-market and sector RS remain explicitly `NOT_IMPLEMENTED_V0_19`.

The run will also test whether Anglo American and Sasol can be recovered from fresh fixed-window acquisition. Any recovery is a new v0.19 observation; v0.18 remains unchanged.

## Expected v0.19 evidence

The run writes:

- `p0_feature_augmented_v0.19.csv`;
- `p0_feature_quarantine_v0.19.csv`;
- `recovered_prior_quarantine_v0.19.csv`;
- `yahoo_symbol_map_v0.19.csv`;
- `price_cache_state_v0.19.csv`;
- `yfinance_batch_log_v0.19.csv`;
- `p0_feature_distribution_v0.19.csv`;
- `p0_asof_distribution_v0.19.csv`;
- `p0_lane_feature_capability_v0.19.csv`;
- `p0_parameter_registry_v0.19.json`;
- `stage_checkpoint_v0.19.json`;
- `summary_v0.19.json`;
- `feature_augmentation_manifest_v0.19.json`.

A successful augmentation still does **not** make automated P0 ready. The next planned scope is `P0_RELATIVE_STRENGTH_AUGMENTATION_AND_LANE_PARAMETER_VALIDATION`.
