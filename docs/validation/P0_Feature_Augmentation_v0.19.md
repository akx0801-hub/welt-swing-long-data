# P0 Feature Augmentation v0.19 — Validation Plan

**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Date:** 2026-08-24  
**Stage:** `P0_FEATURE_AUGMENTATION_AND_PARAMETER_VALIDATION`

## 1. Purpose

v0.19 is a bounded research-partial feature-augmentation run over the frozen 2,037-row v0.16 research snapshot after the v0.18 integrity correction. It does **not** activate P0 qualification, does not create Swing candidates, and does not change Welt-Swing v7.2.

The immediate goals are:

1. re-acquire a clean, closed-bar Yahoo/yfinance daily OHLCV window for all 2,037 research-partial identities through Friday 2026-08-21;
2. test whether the two v0.18 unmatched feature rows — Anglo American and Sasol — are recovered by fresh acquisition without rewriting v0.18 history;
3. persist threshold-neutral multi-day descriptors needed for later six-lane P0 research;
4. measure feature distributions and remaining capability gaps without inventing automated P0 PASS thresholds.

## 2. Frozen predecessor evidence

v0.18 is the input authority for this step:

- input rows: 2,037;
- actual persistent feature matches: 2,035;
- quarantine rows: 2;
- both quarantine reasons: `UNMATCHED_FEATURE_ROW`;
- quarantined identities: Anglo American (`WS:SRC:ZA_TOP40:C46C9A1E2438665A`) and Sasol (`WS:SRC:ZA_TOP40:3CA42D3A25639D8E`);
- P0 not run; zero survivors; automated P0 not ready; Alpha Vantage disabled.

The workflow freezes v0.18 summary/quarantine, the v0.16 partial universe, the audited `price_cache.py`, the existing `feature_builder.py`, Yahoo symbol overrides and `requirements.txt` by Git blob SHA before acquisition.

## 3. Data-source and request discipline

Only `YFINANCE_FREE` / yfinance is permitted. Alpha Vantage is forbidden and has no fallback path.

Acquisition uses the audited `YFinancePriceCacheRunner._process_batch()` primitive, but v0.19 supplies its own fixed-window orchestration so no in-progress 2026-08-24 daily bar can enter the snapshot:

- request start: `2025-05-01`;
- request end, exclusive: `2026-08-24`;
- closed-bar reference date: `2026-08-21`;
- batch size: 100;
- maximum one identical retry per batch;
- one bounded regrouped rescue wave for symbols omitted by a bulk response;
- no serial provider-symbol search and no per-security web-lookup architecture;
- `repair=True` is disabled in this snapshot because the existing repair helper uses a rolling period rather than this fixed cutoff.

`yf_download_batch_invocations` counts calls into the yfinance batch-download method, including identical retries. It is **not** represented as an HTTP-request count; yfinance may perform internal network requests that this runner does not measure.

The runtime SQLite cache is temporary and is not committed.

## 4. Feature policy

The existing local technical conventions are retained: hard-invalid OHLC/negative-volume rows are excluded from feature calculations, and prices/volume receive split-only technical normalization. Only cache state `READY` with complete core feature fields may enter the augmented feature table; all other rows are quarantined fail-closed.

v0.19 adds descriptive observations only, including:

- current RVOL against the preceding 20-session median volume;
- current true range, ATR ratio, gap and close location within the bar;
- 5/10/20-session range compression descriptors;
- 5/20-session true-range means and ratio;
- EMA20/EMA50 slopes;
- consecutive closes above EMA20/EMA50/SMA200;
- days since recent EMA20/EMA50 up/down crosses;
- a recent-low-10 versus prior-low-10 higher-low proxy;
- distances from 20/60-session lows and 20-session high in ATR units;
- recent return extrema;
- maximum true-range / preceding-ATR and volume / preceding-median-volume observations;
- strongest positive 20-session impulse plus post-impulse hold/range descriptors;
- 5/20-session realized return standard deviations and ratio;
- AsOf age versus the fixed 2026-08-21 closed-bar reference.

These fields are observations, not qualification rules.

## 5. Explicitly unimplemented in v0.19

Home-market and sector relative strength are **not** approximated or back-filled from an unrelated benchmark. Every augmented row therefore carries:

- `HomeMarket_RS_Status = NOT_IMPLEMENTED_V0_19`
- `Sector_RS_Status = NOT_IMPLEMENTED_V0_19`

This is a known blocker for a validated automated Quiet-Strength/Relative-Strength lane and remains part of the next-stage scope.

## 6. Parameter governance

`p0_parameter_registry_v0.19.json` must contain:

- `validation_status = HYPOTHESIS_ONLY_NOT_VALIDATED`;
- `p0_numeric_pass_thresholds = []`.

The existing 18% R20 and 30% R60 values remain warning observations only. The approximately 1 ATR breakout distance, approximately 1.3 RVOL confirmation, and approximately 2 ATR climax-range references remain later-stage context only. None becomes a P0 PASS threshold in v0.19.

The six P0 lanes are recorded in `p0_lane_feature_capability_v0.19.csv`. Every lane must remain `Automated_P0_Decision_v0_19 = NOT_ALLOWED`.

## 7. Recovery semantics for the two v0.18 quarantines

If Anglo American and/or Sasol obtain a current fixed-window `READY` cache series and complete features, they are written to `recovered_prior_quarantine_v0.19.csv` as **v0.19 acquisition recovery**. v0.18 remains historically correct and unmodified.

If either still fails mapping, acquisition, QA, staleness or feature completeness, the row stays in the v0.19 quarantine with the current reason. No symbol or data value is guessed to force recovery.

## 8. Required invariants

The workflow fails unless:

- 2,037 input identities are partitioned exactly into augmented + quarantine rows;
- WS_ID is unique and augmented/quarantine sets do not overlap;
- no augmented AsOf is on or after 2026-08-24;
- prior quarantine accounting remains exactly two rows and recovery/still-quarantined sums to two;
- P0 run = false; P0 survivors = 0; lane decisions = false;
- automated P0 ready = false;
- strict U3K frozen = false; full-scan claim = false;
- productive trading authority = false;
- Alpha Vantage = false;
- no FX, news, fundamentals or Scalable execution data are fetched;
- no canonical universe master or v0.18 historical artifact is mutated;
- no numeric P0 PASS threshold is present.

## 9. Outputs

`output_p0_feature_augmentation_v0_19/` contains the augmented feature table, quarantine, prior-quarantine recovery table, Yahoo symbol map, cache state, yfinance batch log, feature distributions, AsOf distribution, six-lane capability matrix, parameter registry, stage checkpoint, summary and output manifest.

## 10. Promotion status

A technically successful v0.19 run is **not** a P0 production or automated-scan promotion. The next intended milestone is `P0_RELATIVE_STRENGTH_AUGMENTATION_AND_LANE_PARAMETER_VALIDATION`, with benchmark/sector-relative-strength architecture and separately validated lane rules. Until that is completed, result wording remains limited to the actually verified coverage; “worldwide best candidate” is forbidden.
