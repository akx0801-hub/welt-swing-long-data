# P0 Breakout / Compression / VCP Contract Design — G-P0-02 v1.00

Status: **PASS — CONTRACT_DESIGN_EVIDENCE_ONLY**. This stage does not supersede G-P0-01/v0.99 and does not authorize P0.

The Master §§29–31 binds Lane 1 conceptually but does not provide a complete deterministic boolean contract. Current v0.93 endpoint features make trend, range/compression, returns and impulse descriptors measurable; measurability is not promoted to a lane rule.

## Pivot audit
Current High20 and High60 are rolling highs including t. Across all 1425 current v0.93 feature rows, cache-derived High20, High60 and the formulas Close_Tech/High20-1 and Close_Tech/High60-1 matched. Therefore current high-distance fields are **not** prior-exclusive pivot identity. PriorHigh20_excl_t and PriorHigh60_excl_t are causally derivable from the read-only governed v0.53 history with 1425/1425 coverage, but remain shadow primitives only.

## Compression feasibility
Because 5/10/20 ranges are nested, non-strict ordering is tautological: Range5 <= Range10 <= Range20 was true 1425/1425. RangeCompression_5_20 < 1 was true 1416/1425; RangeCompression_10_20 < 1 was true 1270/1425. The strict threshold-free relation Range5 < Range10 < Range20 was true 1177 and false 248, so it is non-degenerate in the narrow structural sense, but broad and not a promoted contract component.

## Remaining contract decisions
Eight irreducible decisions remain: base identity/duration, Stage-2 definition, compression definition, prior-pivot definition, pivot proximity, climax definition, excessive-run-up definition, and complete Lane-1 boolean composition. No final parameter value or architecture is selected here.

The ~1 ATR pivot, ~1.3 RVOL and ~2 ATR references remain later-stage references. The 18%/20d and 30%/60d values remain warnings only. No empirical distribution cutoff was derived or promoted.

P0/P1/P2 runs remain zero; no Lane-1 PASS/FAIL, security selection, survivor, ranking or Lane-2 work was produced. Next gate: **BREAKOUT_COMPRESSION_VCP MANAGER CONTRACT DECISION**.
