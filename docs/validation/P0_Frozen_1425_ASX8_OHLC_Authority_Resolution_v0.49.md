# P0 Frozen-1425 ASX-8 Provider OHLC Authority Resolution v0.49

## Gate verdict
**PASS WITH UNRESOLVED ASX-8**

Required start HEAD: `6d4831ef628c1eacb5e840e65059114569703767`.

The v0.48 runtime authority was validated before investigation:
- run 36183320195 / artifact 10885240894
- SQLite SHA-256 `8973ff393db23c7e2d456502c2a71f085f17407dc5ed244dcc04d566c87d4063`
- 144216064 bytes
- integrity_check = ok
- price_daily = 711204
- states = 1425
- READY = 1417
- QUARANTINE = 8

Exact ASX-8 reconciliation: 8/8, missing=0, unexpected=0.

## Common-date diagnostic
A local read-only scan of the v0.48 runtime cache for 2024-11-15 found:
- Frozen bars on date: 1340
- strict OHLC failures: 8
- MIC distribution: XASX = 8
- additional identities outside the exact ASX-8: 0

Therefore v0.48's READY baseline does not contain an additional hidden same-date strict-OHLC failure.

## Session semantics
ASX official documentation establishes that:
1. the closing price is determined by the closing-auction mechanism, or the last trade if the market does not overlap before CSPA;
2. CSPA occurs after continuous trading;
3. CSPA permits trades to execute at the closing price;
4. the ASX ReferencePoint Daily Official List is the official end-of-day trade/quote service and includes closing prices, trade volumes and trade values.

This makes a mixed-session provider construction plausible: High/Low may omit closing-auction executions while Close uses the auction/official close. However, no provider documentation was found proving that Yahoo intentionally defines its daily High/Low that way, and no ASX source was found defining a canonical full-day OHLC bar that deliberately excludes an executed CSPA price from High/Low while using it as Close.

Therefore ASX session mechanics explain a plausible pathway but do **not** authorize reinterpretation of the project's strict OHLC contract.

## Adjustment basis
For all eight challenged rows, Open/High/Low/Close are stored as raw fields and Adj_Close is separate. Dividend=0 and Stock_Split=0 on 2024-11-15. The violation magnitudes range from approximately 0.029% to 0.339%, far beyond binary floating representation noise.

Adjustment/corporate-action mismatch is not supported as the common cause.

## Cross-source findings
### PME
Independent secondary historical data gives 15-Nov-2024:
- Open 207.24
- High 209.86
- Low 205.60
- Close 209.86
- Volume 103408

The challenged provider gives raw O/L/C essentially equal to rounding, but High 209.64 and Volume 65929. This directly confirms the challenged provider daily bar is incomplete/inconsistent for PME. Because the independent source is secondary rather than the ASX Daily Official List or another explicitly authenticated licensed EOD row, it is not used for a cache rewrite in this gate.

PME verdict: **PROVIDER_DATA_DEFECT_CONFIRMED**, still QUARANTINE pending authoritative replacement.

### CBA
A transaction record derived from an ASX announcement reports a 15-Nov-2024 BUY consideration of 155.13, matching the challenged Close to rounding and exceeding challenged High 154.945. This materially corroborates the inconsistency, but it is not a complete daily OHLC authority and therefore does not supply a replacement row.

CBA verdict: **PROVIDER_DATA_UNRESOLVED**.

### QAN
Independent market-close coverage reports Qantas at 8.89 on 15-Nov-2024, corroborating the challenged Close. No independent High/Low row was retrieved.

QAN verdict: **PROVIDER_DATA_UNRESOLVED**.

### ANZ, BSL, BXB, NXT, SDF
No complete independent authoritative 2024-11-15 OHLC row was retrieved in this gate. Provider data remain challenged and unresolved.

Verdict for each: **PROVIDER_DATA_UNRESOLVED**.

## Root-cause assessment
Rejected/not supported:
- FLOAT_PRECISION
- simple adjusted-vs-unadjusted Close mismatch
- same-day split/dividend
- eight independent issuer-specific corporate actions

Supported:
- ASX CSPA is a separate closing phase and produces an executable closing trade.
- common-date concentration is real and confined to the exact eight XASX rows.
- independent PME data demonstrate that at least one challenged provider High/Volume is incomplete while its Close is corroborated.

Best supported architectural hypothesis: a provider/session-coverage or vendor-transformation defect, potentially continuous-session High/Low combined with an auction/official Close. The exact provider transformation has not been proven for all eight, so no blanket correction is authorized.

## Data corrections
None.

No max(High,Close), min(Low,Close), tolerance, interpolation, manual candle, adjustment rewrite or QA-rule weakening was applied.

## Runtime state
No SQLite mutation occurred. The v0.48 byte-bound runtime remains authoritative:
- READY = 1417
- QUARANTINE = 8
- total = 1425
- SHA-256 = `8973ff393db23c7e2d456502c2a71f085f17407dc5ed244dcc04d566c87d4063`

P0_PRICE_CACHE_READY = **NO**.

## Next gate
**P0 FROZEN-1425 ASX-8 ASX DAILY OFFICIAL LIST / LICENSED EOD ACQUISITION GATE**

That gate should acquire only the exact 2024-11-15 official/licensed EOD rows for these eight identities from ASX ReferencePoint/Daily Official List or a clearly licensed independent EOD source. If complete authoritative replacement rows are obtained, a separate controlled cache-correction gate can persist them.

No P0, features, RS, parameter promotion, universe mutation or trading is authorized.
