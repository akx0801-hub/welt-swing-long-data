# P0 Frozen-1425 Runtime Cache Integrity Refreeze v0.47

## Verdict
**PASS**

- Required start HEAD: `50672a0892d0d7d39c6f1dd255aa0af51565d521`
- RUNTIME_CACHE_AUTHORITY_VALID: **YES**
- P0_PRICE_CACHE_READY: **NO**
- Semantic cache state remains **1415 READY / 10 QUARANTINE**.
- No market-data acquisition, P0 execution, feature/RS generation, parameter promotion or Universe mutation occurred.

## v0.46 defect reproduction
The v0.45 artifact was revalidated from workflow run `36138138825`, artifact `10865594502`.

- Artifact ZIP SHA-256: `d5dfeb8250949632d0982ad7272046e9dbca24f0ee650eb8a9c3ba7dc1c29fab`
- v0.45 declared pre-close SQLite SHA-256: `a245c23c7644589ef6c79195b61c13dfdd47bd8b89b9f3ee923de205a73541c0`
- actual finalized artifact SQLite SHA-256: `9e2721e1cc32c8470719271f17e0fac51d9bc88f07edabb499b679d0343a39c9`
- actual bytes: 144216064
- PRAGMA integrity_check: `ok`
- states: 1425
- price_daily rows: 711204

The v0.46 defect is therefore reproduced exactly.

## Root cause and bounded correction
The historical v0.45 harness calculated the runtime SQLite hash before `SQLitePriceCache.close()`, while the cache used WAL mode. The uploaded artifact consequently contained finalized/checkpointed bytes different from the pre-close hash.

Historical v0.45/v0.46 evidence was not rewritten.

A new bounded v0.47 refreeze harness was added. It:
1. downloads only the exact v0.45 artifact;
2. verifies the finalized source SQLite;
3. preserves those already-finalized bytes by exact file copy;
4. validates logical state read-only;
5. closes all validation handles;
6. hashes the stable file twice;
7. uploads that exact file as the new runtime authority candidate.

No price acquisition or provider call exists in this workflow.

An initial diagnostic workflow attempt (`36177681338`) correctly failed before packaging because the new audit harness referenced the wrong historical table name (`price_rows` instead of the actual `price_daily`). The bounded harness was corrected without touching data or calling a provider. Successful refreeze run: `36177809571`.

## State reconciliation
The source v0.45 output matrix and the refrozen SQLite reconcile exactly:

- Frozen members: 1425
- SQLite states: 1425
- READY: 1415
- QUARANTINE: 10
- READY identities missing: 0
- READY identities unexpected: 0
- compared state-field mismatches: 0

Exact ten QUARANTINE states remain:
- WS:XASX:ANZ / ANZ.AX / STRICT_OHLC_RELATION_FAIL
- WS:XASX:BSL / BSL.AX / STRICT_OHLC_RELATION_FAIL
- WS:XASX:BXB / BXB.AX / STRICT_OHLC_RELATION_FAIL
- WS:XASX:CBA / CBA.AX / STRICT_OHLC_RELATION_FAIL
- WS:XASX:NXT / NXT.AX / STRICT_OHLC_RELATION_FAIL
- WS:XASX:PME / PME.AX / STRICT_OHLC_RELATION_FAIL
- WS:XASX:QAN / QAN.AX / STRICT_OHLC_RELATION_FAIL
- WS:XASX:SDF / SDF.AX / STRICT_OHLC_RELATION_FAIL
- WS:XNAS:ECHO / ECHO / SUSPICIOUS_RETURN_NEEDS_REPAIR
- WS:XNAS:MRNA / MRNA / SUSPICIOUS_RETURN_NEEDS_REPAIR

No anomaly was investigated or reclassified in this gate.

## Byte-bound refrozen authority
Successful workflow run: `36177809571`
Artifact: `10882986280`
Artifact ZIP SHA-256: `1d2609551e3fce7f25a4910b949d0215244b5a73bbf915d061d65798e1414902`

Declared refrozen SQLite:
- bytes: **144216064**
- SHA-256: `9e2721e1cc32c8470719271f17e0fac51d9bc88f07edabb499b679d0343a39c9`

Downloaded packaged SQLite:
- bytes: **144216064**
- SHA-256 pass 1: `9e2721e1cc32c8470719271f17e0fac51d9bc88f07edabb499b679d0343a39c9`
- SHA-256 pass 2: `9e2721e1cc32c8470719271f17e0fac51d9bc88f07edabb499b679d0343a39c9`

The packaged SQLite is byte-identical to the finalized v0.45 source SQLite.

Declared SHA == packaged SHA: **PASS**
Declared bytes == packaged bytes: **PASS**
Repeated hash: **PASS**

## Regression test
`tests/test_p0_frozen_1425_runtime_refreeze_v0_47.py` passed in the successful workflow.

The test creates a temporary WAL SQLite database and directly asserts that the connection is closed before the binding hash function can run. This guards the ordering:

`commit/checkpoint/close -> hash -> package`

## Governance
- Frozen Git blob remains `018a03eb4614a197da9d2d566e77f32c61238dad`.
- Frozen SHA-256 remains `54b7a7dacf95b832176c2069ca11c787ce47bed522e2153caf2607bc52804ceb`.
- Market-provider calls: 0
- Alpha Vantage calls: 0
- Scalable calls: 0
- P0 not run.
- Productive=false.
- LONG DEV remains DEV / RESEARCH / SHADOW.

## Next gate
**P0 FROZEN-1425 NON-READY 10 PRICE-QA EXACT REMEDIATION — RESUME**

Do not execute it automatically.
