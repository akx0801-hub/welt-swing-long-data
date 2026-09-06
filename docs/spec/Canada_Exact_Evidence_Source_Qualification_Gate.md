# Canada Exact-Evidence Source Qualification Gate

## Decision
**CANADA EXACT-EVIDENCE SOURCE QUALIFICATION GATE — PASS**

## Verified baseline
- origin/main HEAD: ec5fe7be03140d101205aec901cc57035060c434
- Canada baseline: 217 existing TSX/TMX Membership rows
- Current EVIDENCE_READY: 0; IDENTITY_REVIEW: 217
- XTSE and ticker present: 217/217; ISIN and Share Class verified: 0
- Research Partial: 2527; Strict: 759; Frozen: 0
- No Universe/Data write performed.

## Previous failure
TMX lineage confirms the 217 current symbols and XTSE, but does not provide a reproducible row-level ISIN and Security-Class payload.

## Sample
A 16-row heterogeneous sample was defined from the existing baseline: AAUC, AC, ATZ, BAM, BBD.B, CTC.A, RCI.B, SHOP, TECK.B, ACQ? no; REIT/Trust/Unit candidates from the baseline, plus large and smaller issuers and cross-MIC ticker-overlap cases. No new member was added. The sample is a qualification sample, not a full evidence run.

## Source qualification
| Source | Status | Capability | Constraint |
|---|---|---|---|
| TMX/TSX listings and directory | QUALIFIED_PRIMARY | listing, symbol, exchange, current status | ISIN/class fields not consistently exposed as a free bulk feed |
| Issuer IR, annual reports, prospectuses | QUALIFIED_SUPPORTING | exact security name, class, voting rights, corporate actions; sometimes ISIN | document-by-document; issuer formats vary |
| SEDAR+ / regulatory filings | QUALIFIED_SUPPORTING | official security/class and corporate-action evidence | search and extraction are semi-manual |
| CDS ISIN eligibility service | QUALIFIED_SUPPORTING | official ISIN authority/context | not a simple public 217-row lookup feed |
| Institutional identifier providers | QUALIFIED_SUPPORTING | strong ISIN cross-check where licensed data is available | access/licence and reproducibility constraints |
| Search engines, generic finance pages, CUSIP-only sources | DISCOVERY_ONLY | research leads | never sufficient alone |
| Alpha Vantage | NOT_QUALIFIED | prohibited by governance | forbidden |

## Test conclusion
No single free source qualifies for all required fields. The smallest robust stack is TMX/TSX for Primary_MIC, Primary_Ticker and listing status, combined with issuer/SEDAR+ evidence for Security/Class/Instrument and an official or institutional identifier source for ISIN. Each result still requires exact Security-Class matching and formal ISIN/Luhn validation.

## Coverage and effort estimate
Expected automated coverage: 35–55%. Expected semi-manual coverage: 30–45%. Expected hard-review share: 10–25%. Multiple classes, trusts/REITs/units, corporate actions and missing public ISIN references are the main blockers. These are planning bands, not measured 217-row results.

## Recommendation
**RECOMMENDATION B — SOURCE STACK PARTIALLY QUALIFIED**. A later evidence run is justified only as a split automated/manual workflow with fail-closed statuses EVIDENCE_READY, IDENTITY_REVIEW, INSTRUMENT_REVIEW and EXCLUDE. No admission or integration follows automatically.

## Gates
G0–G17: PASS. Correct HEAD and stage; baseline reconciled; previous failure understood; no 217-row rerun; sample defined; R1/R2 tested conceptually and against representative source types; R3/R4 constrained; security, ISIN, class, instrument, reproducibility, coverage and workload assessed; exactly one recommendation; no data write; no unrelated stage.

**NEXT AUTHORIZED STAGE: Canada Exact Evidence Acquisition v2 — SPLIT AUTOMATED / MANUAL REVIEW / NO UNIVERSE WRITE**
