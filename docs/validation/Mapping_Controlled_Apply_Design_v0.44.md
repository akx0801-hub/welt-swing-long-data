# Mapping Controlled Apply Design v0.44

Stage `CURRENT_MASTER_RESEARCH_PARTIAL_1633_CONTROLLED_MAPPING_APPLY_DESIGN` / `MAPPING_APPLY_DESIGN_ONLY`.

This stage is design only. It does not write `Yahoo_Symbol`, does not change `Mapping_Status`, does not mutate universe or v0.42 evidence, and does not download prices.

## Preconditions already met

- v0.42: 239 HIGH, collisions 0, `Needs_Price_Verification=YES`
- v0.43 sidecar: 239 `PASS` (221 `EXACT`, 18 `GBP_PENCE_EQUIVALENT`)
- Universe slice for those 239: `Yahoo_Symbol` empty, `Mapping_Status=UNMAPPED`
- Universe total remains 1633; 1394 rows are out of scope

## Future apply (not this commit)

A later execution stage may copy `Proposed_Yahoo_Symbol` onto the matching universe row **if and only if** all gates pass.

Allowed write, 239 rows only:

| Field | From | To |
|---|---|---|
| `Yahoo_Symbol` | empty | `Proposed_Yahoo_Symbol` |
| `Mapping_Status` | `UNMAPPED` | `EVIDENCE_CANDIDATE_APPLIED` |
| `Last_Validated` | existing | apply UTC |

Forbidden: `WS_ID`, `ISIN`, `Primary_Ticker`, `Primary_MIC`, `Primary_Currency`, `Name`, `Share_Class`, `Alpha_Symbol`, eligibility, P0, FX, price cache, the other 1394 rows, v0.42 frozen identity columns.

`Mapping_Status` must **not** become `YFINANCE_VERIFIED`. That status is reserved for history-backed verification.

## Gates

1. Evidence row HIGH, decision `CONFIRMED_PROVIDER_SYMBOL_CANDIDATE`
2. Sidecar `Probe_Status=PASS` for the same `WS_ID`
3. Proposed symbols unique (collisions 0)
4. Universe `WS_ID` match, `Yahoo_Symbol` empty, `Mapping_Status=UNMAPPED`
5. Dry-run diff shows exactly 239 `Yahoo_Symbol` fills and zero identity edits
6. Explicit user Freigabe for the execution stage (not this spec)

Fail-closed: any gate miss aborts with no write.

## This spec writes

`docs/validation/Mapping_Controlled_Apply_Design_v0.44.md` only.

`mapping_applied=false`. Next Freigabe is still not apply.
