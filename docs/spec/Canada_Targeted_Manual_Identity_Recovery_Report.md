# Canada Targeted Manual Identity Recovery Report

## Stage decision

**CANADA TARGETED MANUAL IDENTITY RECOVERY — PASS**

This was a bounded, read-only recovery stage for exactly 30 rows selected from the existing 217-row Canada Membership baseline. It created no admission, mapping, eligibility, integration or Universe output.

## Start and authorization

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `724f4cdcc34643279d5cfc1ea8729b612a7b42ed`
- Authorized stage: Canada Targeted Manual Identity Recovery — READ-ONLY / NO UNIVERSE WRITE
- Starting commit: `Canada post evidence manager gate`
- Full Canada baseline: 217
- Research Partial: 2527
- Strict: 759
- Frozen: 0
- Alpha Vantage: prohibited and unused

## Canada baseline and deterministic selection

The baseline was re-isolated from `universe/research_partial_1633.csv` using `Country=Canada`. The result was 217 rows, with the existing XTSE/ticker fields preserved as input values. No new Canadian security was introduced.

The selection rule was declared before recovery:

- +3: existing `Primary_MIC=XTSE` and non-empty ticker
- +3: simple equity naming; no preferred, trust, REIT, unit, ETF/fund, receipt or class/voting marker
- +2: issuer evidence path expected
- +2: filing/annual-report path expected
- +2: identifier cross-check path expected
- +1: no multiple-class marker
- +1: no corporate-action warning in existing notes
- −3: preferred/trust/REIT/unit/ETF/fund/receipt or `.UN` unit marker
- −3: class/voting/multiple-class marker
- tie-break: lexicographic `WS_ID`

The first 30 rows at the maximum score of 14 were selected. This is a deterministic rule-based selection, not a fame-based or discretionary list.

- Selected: 30
- Not selected: 187
- Selected score range: 14
- Selection sidecar: `output_canada_targeted_recovery/CANADA_TARGETED_RECOVERY_SELECTION.csv`

Selected tickers: AAUC, AAV, ABRA, ABX, AEM, AG, AGI, AIF, ALA, ALS, AQN, ARE, ARIS, ARX, ASM, ATD, ATH, ATRL, ATS, AYA, BB, BCE, BDGI, BDT, BHC, BIR, BMO, BNS, BTE, BTO.

## Recovery method and source hierarchy

Each selected row was treated as an independent Security-level case. The existing fields were never overwritten. The review path used:

1. R1 official listing context: TMX Money / TSX quote paths, including symbol and exchange context.
2. R1/R2 supporting paths: issuer investor-relations material, annual reports, prospectus or filing context where available.
3. R2 identifier cross-check paths where available.
4. R3/R4 material only as discovery or cross-check; never as a readiness basis.

For a promoted row, the hard identity key would have to be:

`ISIN + Primary_MIC + Primary_Ticker`

with the same concrete Security and Share Class, formal ISIN/Luhn validation, instrument classification and no unresolved corporate action or collision. A CUSIP, issuer-level match, ticker-only match or ISIN belonging to another share class was not accepted.

The TMX paths used for the selected symbols provide listing/ticker/exchange context, but the selected batch did not produce retained, reproducible Security-level ISIN and Share-Class evidence sufficient for promotion. Therefore the result is fail-closed.

## Results

| Measure | Count |
|---|---:|
| Canada baseline | 217 |
| Selected for recovery | 30 |
| Not selected | 187 |
| Recovery rows reviewed | 30 |
| RECOVERY_READY | 0 |
| RECOVERY_REVIEW | 30 |
| RECOVERY_INSTRUMENT_REVIEW | 0 |
| RECOVERY_EXCLUDE | 0 |
| Final-status sum | 30 |
| Verified ISIN | 0 |
| Verified Share Class | 0 |
| Verified Instrument Type | 0 |
| Verified Primary MIC | 30 |
| Verified Primary Ticker | 30 |
| TRUE_IDENTITY_CONFLICT | 0 |
| ALREADY_PRESENT_EXACT | 0 |
| TICKER_ONLY_CROSS_MIC | 0 within the selected result set |
| Corporate Action cases | 0 |

All 30 selected rows received exactly one final status and a structured review reason in the recovery sidecar. The dominant reasons are:

- `MISSING_ISIN`
- `SHARE_CLASS_UNRESOLVED`
- `INSTRUMENT_TYPE_UNRESOLVED`

Existing XTSE and ticker values are recorded as baseline/verified listing context only; they do not cure the missing Security-level identity fields.

## Recovery yield and scalability

- Recovery Yield: 0/30 = 0.0%
- Exact ISIN Yield: 0/30 = 0.0%
- Share-Class Yield: 0/30 = 0.0%
- Instrument-Type Yield: 0/30 = 0.0%
- Manual Cost: HIGH
- Scalability: LIMITED

The targeted path did not generate a recoverable exact identity in this batch. It nevertheless produced a useful decision result: the failure is not caused by a relaxed threshold or by a missing batch size; even objectively favorable-looking simple XTSE/ticker rows remained blocked by the exact ISIN and Share-Class gates. No second batch is started or implied.

## Manager conclusion

The targeted recovery was unsuccessful as an identity-recovery yield test: 0 of 30 selected rows reached `RECOVERY_READY`. Canada therefore remains a 217-row historical Membership baseline with no conversion-ready output. This result does not prove that all 217 rows are wrong and does not authorize deletion or replacement.

A second recovery batch is not automatically authorized. The appropriate next decision is a separate manager review of whether Canada should remain parked or be rebuilt through a separately governed current-source admission policy. No Canada Admission, Mapping or Integration decision is made here.

**TARGETED RECOVERY UNSUCCESSFUL — MANAGER REVIEW**

**NEXT: READY FOR SEPARATE CANADA TARGETED RECOVERY MANAGER GATE**

## No-touch confirmation

No Membership, Research Partial, Strict, Frozen, Universe/Data Master, History, Liquidity, Eligibility, Scan/U3K, AU-1, US-1, US-2 or Welt-Swing v7.2 file was changed. No new Canadian member was added. No Batch 2, other population or follow-on stage was started.

## Quality gates

- G0 Correct `origin/main` HEAD: PASS
- G1 Correct authorized stage: PASS
- G2 Canada baseline remains 217: PASS
- G3 Selection rule documented before recovery: PASS
- G4 Selected count between 20 and 40: PASS
- G5 Selection deterministic: PASS
- G6 Only selected rows researched: PASS
- G7 Qualified source hierarchy respected: PASS
- G8 Exact Security checked: PASS
- G9 Share Class checked: PASS
- G10 Instrument Type checked: PASS
- G11 ISIN formally and semantically checked: PASS
- G12 Primary MIC/Ticker checked: PASS
- G13 Corporate Actions checked: PASS
- G14 Collision QA completed: PASS
- G15 Exactly one final status for every selected row: PASS
- G16 No Universe/Data Master write: PASS
- G17 No second batch or unrelated stage started: PASS

