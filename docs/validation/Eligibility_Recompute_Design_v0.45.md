# Eligibility Recompute Design v0.45

Stage `CURRENT_MASTER_RESEARCH_PARTIAL_1633_ELIGIBILITY_RECOMPUTE_DESIGN` / `ELIGIBILITY_DESIGN_ONLY`.

This stage is design only. It does not recompute eligibility, does not mutate `Universe_Status`, does not download history, does not touch `SWING_U3K_FROZEN`, and does not run P0.

## Why recompute is blocked

The 239 v0.44 rows now have `Yahoo_Symbol` and `Mapping_Status=EVIDENCE_CANDIDATE_APPLIED`. That is mapping, not eligibility.

Still missing for those 239:

- price history / cache (`price_download` remains false)
- liquidity evidence
- Scalable still `NOT_VERIFIED`
- `Share_Class` empty on the universe row (class lives only on v0.42 evidence)
- mapping is not `YFINANCE_VERIFIED`

v0.37 already forbade eligibility calculation on stale price-derived evidence. Filling Yahoo does not lift that ban.

Current 1633 snapshot: all `Universe_Status=ACTIVE_VERIFIED`. A recompute that promoted or demoted from that flag would be a new productive decision. Not in this spec.

## Future eligibility (not this commit)

A later execution stage may recompute eligibility **only after**:

1. dedicated history-download stage for the 239 (and any other mapped rows in scope)
2. liquidity/FX audit against that history
3. explicit Freigabe separate from this spec
4. dry-run showing which WS_IDs would change `Universe_Status` / Scalable / U3K-input — zero silent promotions

Fail-closed: no history → no eligibility write.

Forbidden still: `Primary_Ticker` identity, v0.42 frozen columns, U3K frozen files, productive trading flags, P0, Sector RS.

## This spec writes

`docs/validation/Eligibility_Recompute_Design_v0.45.md` only.

`eligibility_promoted=false`. Next Freigabe is still not eligibility and still not history download.
