# Welt-Swing Long DEV — Non-READY Remediation v0.2

## Scope

This step follows the completed 85-row Non-READY Diagnostic and implements
three controlled actions:

1. evidence remediation of the 10 DOWNLOAD_FAILED/STALE listing cases;
2. a shadow QA policy for the 23 isolated-invalid-bar candidates;
3. separate classification of suspicious-return events.

A further critical identity correction is included for Sasol: the Top-40
ordinary share is `SOL`, not the distinct BEE share class `SOLBE1`.

No price/history request is made in this step. No cache state is automatically
promoted to READY. P0 remains OFF.

## Listing and mapping decisions

### Excluded as stale, delisted or retired

- Insignia Financial (`IFL.AX`) — ASX removal 29 Apr 2026.
- National Storage REIT (`NSR.AX`) — ASX removal 12 May 2026.
- Grupo Elektra (`ELEKTRA.MX`) — share registration cancelled in Apr 2026.
- Arvida equity (`ARV.NZ`) — ceased NZX quotation after acquisition.
- Manawa Energy equity (`MNW.NZ`) — ceased NZX quotation after acquisition.
- Clearway Energy Class A (`CWEN-A`) — converted 1:1 into Class C on 1 May
  2026. The frozen source universe already contains the canonical Class C row
  `WS:US:CWEN`, so the retired Class A row is inactivated instead of being
  remapped onto a duplicate `CWEN` provider symbol.

No replacement constituent is injected during this data-remediation step.

### Active mapping corrections

- Block ASX: `XYX.AX` → `XYZ.AX`.
- ALFA / Sigma Foods: `ALFAA.MX` → `SIGMAFA.MX`.
- Goodman Property Trust / Goodman NZ: `GMT.NZ` → `GNZ.NZ`.
- Sasol: `SOLBE1.JO` → ordinary Top-40 share `SOL.JO`.

### Current symbol, refresh only

IES Holdings remains current under `IESC`. Its cache should be refreshed rather
than remapped or excluded. IES announced a two-for-one split with distribution
after trading on 21 Aug 2026.

## Shadow filtered-bar QA policy

The existing raw cache is immutable.

A quarantine with malformed OHLC/volume may qualify as a **shadow**
filtered-ready candidate only if all conditions hold:

- at most 2 invalid bars;
- invalid share <= 1%;
- at least 260 valid bars remain;
- latest valid history is fresh;
- zero suspicious-return events remain.

The first diagnostic found 23 rows matching the isolated-bar shape. Three also
carry suspicious scale anomalies, therefore only 20 are expected to pass the
strict shadow policy.

The feature builder already excludes technically invalid bars. This workflow
computes real shadow feature rows for those 20 names and merges them with the
3,578 existing READY feature rows:

**3,598 effective shadow feature rows**

This does not yet change cache status. Promotion of the QA rule into
`price_cache.py` remains a separate validation decision.

## Suspicious-return classification

The suspicious-event file is grouped by security and classified separately.

- repeated approximately 100x / 0.01x transitions:
  `LIKELY_PROVIDER_SCALE_SWITCH_X100`;
- single extreme move:
  `SINGLE_EXTREME_MOVE_EVENT_RESEARCH`;
- multiple extreme moves:
  `MULTI_EXTREME_MOVE_EVENT_RESEARCH`;
- Monster Beverage:
  explicit evidence override `CONFIRMED_SPLIT_RELATED_PROVIDER_MIX`, followed
  by a targeted full refresh.

No suspicious-return series is auto-normalized.

## Targeted refresh queue

A separate next-step queue is created for six active securities:

- Block ASX (`XYZ.AX`)
- Sigma Foods (`SIGMAFA.MX`)
- Goodman NZ (`GNZ.NZ`)
- Sasol ordinary (`SOL.JO`)
- IES Holdings (`IESC`)
- Monster Beverage (`MNST`)

Those are the only names that should receive a targeted full-history refresh
next. The whole universe should not be downloaded again.

## Expected state after remediation

- source master rows: 3,664
- active before: 3,663
- stale/delisted/retired exclusions: 6
- active after evidence remediation: 3,657
- provider/successor remaps: 4
- refresh-only listing case: 1
- strict filtered-bar shadow candidates: 20
- base READY: 3,578
- effective shadow READY/features if QA policy were later approved: 3,598
- effective shadow coverage of 3,657 active rows: about 98.39%
- automatic READY promotions in this step: 0
- P0: OFF
- productive trading authority: NO
- Alpha Vantage: forbidden

## Outputs

- `universe/Welt-Swing-Universe-Master-RemediatedData-v0.8.csv`
- `universe/Welt-Swing-Universe-Master-RemediatedData-v0.8.xlsx`
- `output_non_ready_remediation/summary_v0.2.json`
- `output_non_ready_remediation/listing_and_mapping_remediation_audit_v0.2.csv`
- `output_non_ready_remediation/qa_filtered_bar_policy_candidates_v0.2.csv`
- `output_non_ready_remediation/qa_filtered_feature_additions_v0.2.csv`
- `output_non_ready_remediation/effective_features_shadow_v0.2.csv`
- `output_non_ready_remediation/suspicious_event_classification_v0.2.csv`
- `output_non_ready_remediation/targeted_refresh_queue_v0.2.csv`
