# Canada Post-Identity Manager Gate

DECISION: RECOMMENDATION A

## Verified state
HEAD: 6a08268dcf9b6b03a6a11b78ae0c13c2f7d00419
Canada baseline: 217; CONVERSION_READY 0; IDENTITY_REVIEW 217; INSTRUMENT_REVIEW 0; EXCLUDE 0. XTSE and ticker present 217/217; ISIN, Instrument_Type and Share_Class unresolved.

## Decision
The problem is a solvable exact-evidence gap, not yet a reason to discard the official 217-row TSX baseline. A bounded evidence stage is justified because the population is officially reproducible, materially diversifies the universe, and can fail closed row by row. Legacy revalidation is not required first; it should be included only as a read-only lineage check within the evidence stage.

Option B is rejected: the 217-row official TMX baseline is sufficiently reliable for evidence work. Option C is rejected: parking leaves a documented developed-market gap unresolved.

## Controls
Use R1 official TSX/TMX, issuer, regulatory and security documents; R2 institutional identifier sources; R3 strong secondary only when unambiguous; R4 discovery only. Require ISIN + Primary_MIC + Primary_Ticker, exact security/class, no CUSIP fallback, no ticker-only match, and fail-closed statuses EVIDENCE_READY, IDENTITY_REVIEW, INSTRUMENT_REVIEW or EXCLUDE.

## Gates
G0-G17 PASS. No evidence acquisition was executed; no Membership, Research Partial, Strict, Frozen, History, Liquidity, Eligibility or Universe data was changed.

**NEXT AUTHORIZED STAGE: Canada Exact Evidence Acquisition — READ-ONLY / NO UNIVERSE WRITE**
