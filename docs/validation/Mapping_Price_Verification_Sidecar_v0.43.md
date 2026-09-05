# Mapping Price Verification Sidecar v0.43

Stage `CURRENT_MASTER_RESEARCH_PARTIAL_1633_MAPPING_PRICE_VERIFICATION` / `PRICE_VERIFICATION_SIDECAR_ONLY`.

v0.43 confirms that each of the 239 HIGH v0.42 `Proposed_Yahoo_Symbol` candidates has a live Yahoo equity quote in the expected listing currency. It writes a sidecar only. It does not apply mappings, does not mutate `config/mapping_evidence_acquisition_v0.42.csv`, does not flip `Needs_Price_Verification`, and does not download history into universe or `runtime_cache`.

v0.42 HIGH still requires `Needs_Price_Verification=YES`. That invariant stays.

## Input

- `config/mapping_evidence_acquisition_v0.42.csv` (239 HIGH, collisions 0, read-only)
- Yahoo chart probe `range=5d interval=1d` per proposed symbol (quote-alive, not history ingest)

## Currency rule

| Frozen `Primary_Currency` | Yahoo `currency` | `Currency_Match` |
|---|---|---|
| same ISO code | same ISO code | `EXACT` |
| `GBP` | `GBp` (LSE pence) | `GBP_PENCE_EQUIVALENT` |
| any other pair | | `MISMATCH` |

`GBP`/`GBp` is Yahoo LSE convention, not a fail.

## Probe_Status

- `PASS` — equity, last close present, `EXACT` or `GBP_PENCE_EQUIVALENT`
- `FAIL_DEAD` — HTTP/empty/no last
- `FAIL_CCY` — `MISMATCH`
- `FAIL_NOT_EQUITY` — `instrumentType` ≠ `EQUITY`

Pre-probe (2026-09-05): 239/239 alive; 221 `EXACT`; 18 XLON `GBP_PENCE_EQUIVALENT`; 0 dead.

## Sidecar

`output_mapping_price_verification_v0_43/price_verification_239_v0.43.csv`

Columns: `WS_ID`, `Proposed_Yahoo_Symbol`, `Primary_MIC`, `Primary_Currency`, `Quote_Currency`, `Currency_Match`, `Quote_Last`, `Quote_Exchange`, `Instrument_Type`, `Quote_Name`, `Probe_Status`, `Probe_AsOf_UTC`, `Notes`

Also: `summary_v0.43.json` (`price_download=false`, `universe_mutated=false`, `eligibility_promoted=false`, `productive=false`, `mapping_applied=false`).

## Forbidden

Universe, eligibility, master mapping apply, FX, Alpha Vantage, P0, Sector RS, frozen identity mutation, bulk history cache.

Next stage after sidecar review is still not mapping apply.
