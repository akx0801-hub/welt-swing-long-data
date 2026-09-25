# P0 Frozen-1425 Non-Ready 10 Price-QA Exact Remediation v0.46

## Verdict
**FAIL CLOSED**

Required start HEAD: `018ff14b158807257175134db5286a099c6ed005`.

The exact ten v0.45 non-ready identities reconcile 10/10 with missing=0 and unexpected=0. The gate then encountered an authority-integrity failure before anomaly-level remediation was permitted.

## Authority integrity failure
The downloaded authoritative v0.45 Actions artifact is exactly the named artifact:
- run: 36138138825
- artifact: 10865594502
- artifact ZIP SHA-256: `d5dfeb8250949632d0982ad7272046e9dbca24f0ee650eb8a9c3ba7dc1c29fab` — PASS

But its extracted runtime SQLite:
- path: `runtime_cache/p0_frozen_1425_v0_45.sqlite`
- size: 144216064 bytes — matches manifest
- expected SHA-256 from v0.45 manifest: `a245c23c7644589ef6c79195b61c13dfdd47bd8b89b9f3ee923de205a73541c0`
- actual SHA-256 from authoritative artifact: `9e2721e1cc32c8470719271f17e0fac51d9bc88f07edabb499b679d0343a39c9`
- SQLite PRAGMA integrity_check: `ok`
- cache states: 1425
- state counts: READY=1415, QUARANTINE=10

All bounded v0.45 output files covered by `output_hashes` match their declared SHA-256 values. The mismatch is isolated to the runtime SQLite byte hash.

## Reproducible implementation evidence
The persisted v0.45 execution script computes `sha256_file(db_path)` while the `SQLitePriceCache` remains open, and calls `cache.close()` later. The cache implementation enables SQLite WAL mode.

Therefore the v0.45 manifest binds a pre-close SQLite byte state, while the uploaded artifact contains the post-close/checkpoint file. This is an evidence-packaging / runtime-cache-integrity implementation defect in v0.45. It is **not** evidence of a defect in closed History QA v1 or Liquidity QA v1.

## Consequence
The gate instruction requires FAIL CLOSED if v0.45 is internally inconsistent. Therefore:
- no ASX offending-date rows were promoted as authoritative remediation evidence;
- ECHO/MRNA suspicious-return dates were not reclassified;
- no provider refetch was performed;
- no external evidence was collected;
- no price data was changed;
- all ten retain QUARANTINE.

Per-security verdict for all ten: **QUARANTINE_RETAINED**.

## Final state
- READY: 1415
- QUARANTINE: 10
- Total: 1425
- P0_PRICE_CACHE_READY: **NO**
- Frozen membership unchanged.
- Provider mappings unchanged.
- Market-provider calls: 0
- Alpha Vantage calls: 0
- Scalable calls: 0
- P0 not run.
- Feature/RS/parameter capability not promoted.
- Productive=false.

## Next gate
**P0 FROZEN-1425 V0.45 RUNTIME-CACHE INTEGRITY CORRECTION / REFREEZE GATE**

That gate should reproduce/freeze the exact v0.45 runtime-cache state with the SQLite connection fully closed/checkpointed before hashing and publishing the authoritative SHA-256, without changing Frozen membership or re-running P0. Only after the runtime-cache authority is internally consistent should the exact-ten anomaly investigation resume.
