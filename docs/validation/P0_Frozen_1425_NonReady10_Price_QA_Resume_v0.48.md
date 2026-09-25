# P0 Frozen-1425 Non-Ready 10 Price-QA Resume v0.48

## Verdict
**PASS WITH REMAINING QUARANTINE**

Required gate start HEAD: `80f9637c5bc13a274d26b4126e778ee87b0bdc79`.

The v0.47 byte-bound runtime authority was validated before anomaly work:
- runtime SHA-256: `9e2721e1cc32c8470719271f17e0fac51d9bc88f07edabb499b679d0343a39c9`
- bytes: 144216064
- PRAGMA integrity_check: ok
- states: 1425
- price_daily rows: 711204
- READY: 1415
- QUARANTINE: 10

Exact-10 reconciliation: 10/10, missing=0, unexpected=0.

## ASX-8 findings
All eight anomalies occur on **2024-11-15** and the normal bounded provider refetch reproduced the raw OHLCV exactly. The repair=True bounded refetch produced no replacement rows.

Persisted violations:
- ANZ.AX: High 32.3400001526 < Close 32.4500007629; abs 0.1100006104; relative 0.338985%
- BSL.AX: High 20.9099998474 < Close 20.9500007629; abs 0.0400009155; relative 0.190935%
- BXB.AX: High 19.2649993896 < Close 19.3099994659; abs 0.0450000763; relative 0.233040%
- CBA.AX: High 154.9450073242 < Close 155.1300048828; abs 0.1849975586; relative 0.119253%
- NXT.AX: Low 16.6450004578 > Close 16.6399993896; abs 0.0050010681; relative 0.029009%
- PME.AX: High 209.6399993896 < Close 209.8600006104; abs 0.2200012207; relative 0.104832%
- QAN.AX: High 8.8699998856 < Close 8.8900003433; abs 0.0200004578; relative 0.224977%
- SDF.AX: Low 5.6300001144 > Close 5.6199998856; abs 0.0100002289; relative 0.176527%

These are not floating-point noise: the differences are economically material relative to binary representation error and reproduce from the provider. No row has a split or dividend on the anomaly date. The common date across unrelated ASX issuers indicates a common source/session-semantics problem rather than eight issuer-specific corporate actions.

ASX's official market documentation states that the closing price is established by the Closing Single Price Auction (or the last ASX trade when no auction trade occurs), while the daily price range is the highest/lowest traded price. The project did not obtain an authoritative corrected per-security OHLC row for these eight, so no manual normalization or rule weakening is permitted.

Classification: **OTHER_EVIDENCED / provider daily-OHLC semantics unresolved**.
Per-security verdict: **PROVIDER_DATA_UNRESOLVED**.
All eight remain QUARANTINE.

No closed History QA v1 or Liquidity QA v1 implementation defect was established.

## ECHO
Persisted and provider-refetched prices reproduce exactly:
- 2025-08-25 close: 29.8799991608
- 2025-08-26: O 54.1100006104 / H 55.1899986267 / L 50.6199989319 / C 50.8699989319
- raw close return: +70.2476585%
- volume: 46,579,100
- split: 0
- dividend: 0
- 2025-08-27 close: 58.7599983215

Issuer primary evidence dated 2025-08-26 documents EchoStar's approximately $23 billion spectrum transaction with AT&T.

Classification: **GENUINE_MARKET_MOVE**.
Verdict: **LEGITIMATE_EVENT_READY**.

## MRNA
Persisted and provider-refetched prices reproduce exactly:
- 2026-08-18 close: 62.9599990845
- 2026-08-19: O 116.0199966431 / H 176.6600036621 / L 114.4599990845 / C 174.3800048828
- raw close return: +176.9695162%
- volume: 199,252,300
- split: 0
- dividend: 0
- 2026-08-20 close: 133.3200073242

Issuer primary evidence dated 2026-08-19 documents positive Phase 3 INTerpath-001 melanoma topline results.

Classification: **GENUINE_MARKET_MOVE**.
Verdict: **LEGITIMATE_EVENT_READY**.

## Data corrections
No OHLC value was edited, interpolated or normalized.
Data corrections: **0**.

Only two cache-state records changed:
- ECHO: QUARANTINE/SUSPICIOUS_RETURN_NEEDS_REPAIR -> READY/VERIFIED_EXTREME_RETURN
- MRNA: QUARANTINE/SUSPICIOUS_RETURN_NEEDS_REPAIR -> READY/VERIFIED_EXTREME_RETURN

All price_daily rows remain unchanged.

## Final runtime authority
Workflow run: 36183320195
Artifact: 10885240894
Artifact ZIP SHA-256: `0be6ca06691f2715c7c663bd7abfacbe1d65553d5debed4b6ba87b766918cfab`

Final runtime SQLite:
- bytes: 144216064
- declared SHA-256: `8973ff393db23c7e2d456502c2a71f085f17407dc5ed244dcc04d566c87d4063`
- packaged/retrieved SHA-256: `8973ff393db23c7e2d456502c2a71f085f17407dc5ed244dcc04d566c87d4063`
- hash repeat: PASS
- integrity_check: ok
- states: 1425
- price_daily rows: 711204
- READY: 1417
- QUARANTINE: 8

Byte binding: **PASS**.

## Decision
P0_PRICE_CACHE_READY = **NO**

The remaining blockers are exactly the eight ASX provider-OHLC inconsistencies. No reduced P0 population is authorized.

## Governance
Frozen membership remains 1425 and is unchanged.
Provider mappings are unchanged.
Diagnostic provider calls: 6 bounded calls, only Exact-10 symbols.
Alpha Vantage calls: 0.
Scalable calls: 0.
P0 was not run.
Features, RS and parameters were not promoted.
LONG DEV remains DEV / RESEARCH / SHADOW.
productive=false.

## Next gate
**P0 FROZEN-1425 ASX-8 PROVIDER OHLC AUTHORITY RESOLUTION GATE**

Do not execute it automatically.
