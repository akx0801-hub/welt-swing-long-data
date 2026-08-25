# WELT-SWING LONG DEV — CURRENT HANDOFF

**Updated:** 2026-08-25 07:08 CEST  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE

## Authority

Authoritative DEV master:
`docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Welt-Swing v7.2 remains unchanged and solely authoritative for productive Swing decisions.

## Latest completed checkpoint — v0.19

Current main:
`350b20d91917c81bae1092b1cdd902ba5b547be7`

Commit:
`Augment P0 research-partial features v0.19`

Confirmed v0.19:
- run status `P0_FEATURE_AUGMENTATION_V0_19_COMPLETE`
- input rows 2,037
- augmented feature rows 2,037
- feature quarantine 0
- prior v0.18 quarantine 2
- recovered prior quarantine 2
- Anglo American recovered as `AGL.JO`
- Sasol recovered as `SOL.JO`
- cache status READY 2,037
- 21 normal yfinance batch invocations
- rescue batches 0
- retries 0
- P0 run false
- P0 survivors 0
- automated P0 ready false
- numeric P0 pass thresholds 0
- Alpha Vantage false
- strict U3K frozen false
- full-scan claim false

## v0.19 AsOf audit

- 2,036 rows: 2026-08-21
- 1 row: 2026-08-20

The one lagging identity is:
- Webster Bank
- `WS:US:WBS`
- Yahoo `WBS`
- Primary universe `US_SP1500`

No reason for the missing 2026-08-21 bar is inferred.

## Next implementation checkpoint — v0.20

`P0_RELATIVE_STRENGTH_AUGMENTATION_AND_LANE_PARAMETER_VALIDATION`

v0.20:
- performs no network calls;
- consumes the frozen v0.19 feature output;
- excludes Webster Bank fail-closed from synchronized RS calculations;
- computes early-discovery Home-Market-RS from leave-one-out medians within `Primary_Universe_Index`;
- explicitly does not claim an official benchmark-index return;
- records positive 20d/60d RS only as the Lane-4 RS component;
- leaves Sector RS as `RS_NOT_VERIFIED_NO_SECTOR_METADATA`;
- emits descriptive lane-parameter evidence without promoting any quantile to a pass threshold;
- keeps P0 run false and survivors 0.

Next planned stage after successful v0.20:
`P0_LANE_PARAMETER_SHADOW_VALIDATION_AND_SECTOR_RS_PREP`.

Allowed later result wording:
`bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage`

Forbidden:
`weltweit bester Kandidat`.
