# History Download Design v0.46

Stage `CURRENT_MASTER_RESEARCH_PARTIAL_1633_HISTORY_DOWNLOAD_DESIGN` / `HISTORY_DOWNLOAD_DESIGN_ONLY`.

This stage is design only. It does not call yfinance, does not write `runtime_cache/*.sqlite`, does not mutate universe, and does not recompute eligibility.

v0.43 was a 5-day quote probe. That is not history.

## Scope if a later stage runs

Only the 239 `EVIDENCE_CANDIDATE_APPLIED` rows. Not the 1296 `UNMAPPED`. Not a silent 1633 refresh.

The 79 `YFINANCE_VERIFIED` rows stay out of this first slice.

Reuse existing `scripts/price_cache.py` / `SQLitePriceCache` / `YFINANCE_FREE`. Target file `runtime_cache/` remains gitignored. Alpha Vantage is forbidden.

v0.38 history contract still applies to a later run: daily OHLCV, cutoff = previous UTC day, XLON GBp scale 0.01, no identity rewrite, no ADR substitution.

## Still forbidden in a later run until extra Freigabe

- `Mapping_Status` → `YFINANCE_VERIFIED`
- eligibility / `Universe_Status`
- `SWING_U3K_FROZEN`
- P0 / Sector RS
- committing sqlite blobs

QA sidecar only: bars count, last date, currency, FAIL/PASS_HISTORY. Fail-closed per symbol; one miss does not invent a ticker.

## This spec writes

`docs/validation/History_Download_Design_v0.46.md` only.

`price_download=false`. Next Freigabe is still not the download.
