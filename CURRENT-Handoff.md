# WELT-SWING LONG DEV — CURRENT HANDOFF

**Updated:** 2026-08-24 14:29 CEST  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE

## 1. Authority and version separation

### Authoritative DEV master specification

`docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Original secured specification currently stored in the repo as:

`docs/spec/Welt-Swing-Long-DEV-v0.1-2026-08-23-1.docx`

Specification version: **WELT-SWING LONG DEV v0.1**  
Specification freeze date: **2026-08-23**

Rules:

- Read the authoritative DEV master specification before continuing Welt-Swing Long development.
- Do not reconstruct the specification from memory when the original artifact is available.
- Do not silently modify v0.1. Material rule changes require a new specification version and explicit validation/promotion.
- Repo implementation versions such as v0.8/v0.9 are **not** prompt/specification versions.
- **Welt-Swing v7.2 remains unchanged and alone productive-authoritative for real Swing trade decisions until explicit later promotion.**
- Alpha Vantage remains forbidden: `ALPHA_VANTAGE_ALLOWED = FALSE`.

## 2. Current repository checkpoint

Repository: `akx0801-hub/welt-swing-long-data`  
Branch: `main`  
Current repo HEAD after master-spec upload: `80607339edf728480d43208e379fb5cab1b67bdb`

Latest completed technical implementation checkpoint remains:

**Instrument Resolution ASX v0.8**

Authoritative v0.8 evidence:

- `docs/validation/Instrument_Resolution_ASX_v0.8.md`
- `output_instrument_resolution_v0_8/summary_v0.8.json`
- `output_instrument_resolution_v0_8/remaining_review_by_segment_v0.8.csv`

Confirmed v0.8 state:

- source manual rows from v0.7: **730**
- Australia rows resolved: **63 / 63**
- ASX strict PASS: **53**
- ASX strict FAIL: **10**
- ASX unresolved: **0**
- remaining instrument-review rows: **667**
- strict candidates v0.7: **1,967**
- strict candidates v0.8: **2,020**
- `strict_freeze_allowed = false`
- `p0_run = false`
- `productive_trading_authority = false`
- `alpha_vantage_allowed = false`
- no price or FX downloads were performed in v0.8
- no per-security web calls were performed in v0.8

Remaining review queue:

| Segment | Rows |
|---|---:|
| CA_TSX | 105 |
| EU_STOXX600 | 365 |
| HK_HSI | 82 |
| KR_KOSPI200 | 92 |
| MX_IPC | 6 |
| ZA_TOP40 | 17 |
| **Total** | **667** |

## 3. Why P0 is still blocked

The DEV master specification requires the strict universe to contain eligible, sufficiently verified securities. `Instrument_Type = UNKNOWN` is not a strict PASS. Therefore the remaining 667 instrument cases must not be silently promoted merely to obtain a frozen U3K.

Until the instrument gate is sufficiently resolved:

- no strict U3K freeze,
- no claim of a complete global P0 scan,
- no productive trade authority.

## 4. Next technical step — v0.9

Next step: **Primary-Market Bundle Probe v0.9**.

Purpose:

- consume only the frozen 667-row v0.8 remaining-review queue,
- acquire official/bourse-level primary-market evidence in bounded bulk form,
- avoid per-security web requests,
- preserve all existing v0.8 eligibility decisions,
- make **zero eligibility changes in the probe itself**,
- prepare evidence for a later classification step.

Planned markets:

- Canada / TSX
- Europe / STOXX Europe 600
- Hong Kong / HKEX
- Korea / KRX
- Mexico / BMV
- South Africa / JSE

Operational request discipline:

- maximum one official/bourse-level probe request per remaining market,
- maximum six external source requests total,
- no Alpha Vantage,
- no price downloads,
- no FX downloads,
- no per-security web calls,
- no P0 execution.

Expected invariant after v0.9 probe:

- remaining source queue starts at **667**,
- strict candidates remain **2,020**,
- `decisions_changed = 0`,
- strict freeze remains false,
- P0 remains off.

## 5. Planned sequence after v0.9

1. Run v0.9 primary-market evidence probe.
2. Review probe outputs and source semantics.
3. Build a separate classification/remediation step only where official source fields have documented instrument-type meaning.
4. Reduce the 667-row queue without blanket or name-based assumptions.
5. Recompute strict candidate state.
6. Freeze `SWING_U3K_FROZEN` only when the master-spec eligibility requirements are actually satisfied.
7. Only then continue into P0 parameterisation/validation and the `U → P0 → P1 → P2 → SHORTLIST FREEZE → P3 → P4 → P5` funnel.

## 6. Resume rule for a new chat/session

Before doing new work:

1. Read this `CURRENT-Handoff.md`.
2. Read the authoritative master specification under `docs/spec/`.
3. Read the newest relevant validation summary/output in the repo.
4. Confirm current `main` HEAD and whether a newer implementation checkpoint supersedes v0.8.
5. Resume from the smallest valid next stage; do not restart from an obsolete handoff.

Older handoffs remain historical provenance only when a newer repo checkpoint exists.

## 7. Productive-trading boundary

This repository and all v0.x implementation work remain **DEV / SHADOW**. A future DEV result does not itself authorize a real trade. Real Swing decisions continue to require the authoritative Welt-Swing v7.2 process until an explicit validated promotion occurs.
