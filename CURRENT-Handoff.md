# WELT-SWING LONG DEV — CURRENT HANDOFF

**Updated:** 2026-08-24 16:04 CEST  
**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE

## Authority

Authoritative DEV master specification:

`docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md`

Specification: **WELT-SWING LONG DEV v0.1**, frozen 2026-08-23.

Welt-Swing v7.2 remains unchanged and alone productive-authoritative for real Swing decisions until explicit validated promotion.

## Current repo checkpoint

Latest completed technical checkpoint:

**JSE Equities ISIN Bulk Probe v0.11**

Repo HEAD after v0.11 output commit:

`30a2c260b6246de7c7d13e8eae0d4503822bb40c`

Commit:

`Probe JSE equities ISIN bulk source v0.11`

## Confirmed v0.11 result

- run status: `JSE_ISIN_BULK_PROBE_V0_11_COMPLETE_WITH_EVIDENCE`
- source manual rows: **667**
- ZA_TOP40 target rows: **17**
- strict candidates: **2,020**
- remaining manual rows: **667**
- decisions changed: **0**
- JSE folder HTTP: **200**
- JSE ZIP HTTP: **200**
- exactly one `isinfull_e.zip` link discovered
- exactly one archive member parsed
- external reference requests: **2 / 2**
- strict freeze: **false**
- P0: **false**
- no per-security requests
- no price/FX downloads
- Alpha Vantage forbidden
- canonical master unchanged

The current archive member is `isinfull_e`; v0.11 recorded 4,070,331 uncompressed bytes and cp1252 text samples.

The sample contains an explicit fixed-width instrument-type area, e.g. `ETF`, followed by a JSE alpha code. This is consistent with JSE's separately published Instrument Type semantics, but v0.11 deliberately made no classification.

## Remaining review queue

| Segment | Rows |
|---|---:|
| CA_TSX | 105 |
| EU_STOXX600 | 365 |
| HK_HSI | 82 |
| KR_KOSPI200 | 92 |
| MX_IPC | 6 |
| ZA_TOP40 | 17 |
| **Total** | **667** |

## Source blocks already established

### Korea / KRX
Anonymous Data Marketplace bulk POST remains HTTP 400. No further blind retries in the current free/no-credential route.

### South Africa / JSE
The public Equities ISIN bulk file is reachable. This is now the active remediation lane.

## Next step

**v0.12 — JSE Instrument Resolution**

v0.12 re-downloads the same official JSE bulk source under the same bounded two-request rule and validates the complete fixed-width record structure before reading any Instrument Type.

Only after structural validation:

- exact JSE alpha-code matches are used,
- `Aord`, `Bord`, `Nord`, `Ordinary` are strict PASS,
- clearly non-ordinary types such as `DepRec`, `ETF`, `LU`, `PS`, `UT`, `PL`, debentures/warrants/options are strict FAIL,
- generic or unknown types remain `NOT_VERIFIED`.

The 17 ZA rows currently have blank `Primary_Ticker`; the frozen `.JO` symbol is used only as a lookup key and must exact-match the official JSE Alpha Code.

If source, layout, identity match, or type semantics are not deterministic, the row remains unresolved.

## Resume rule

1. Read this file.
2. Read the master spec.
3. Read the newest `summary_v0.x.json`.
4. Confirm current `main` HEAD.
5. Resume from the smallest valid next stage.

Never regress to an obsolete instrument-resolution workflow.
