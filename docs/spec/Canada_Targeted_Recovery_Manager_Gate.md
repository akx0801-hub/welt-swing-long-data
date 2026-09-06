# Canada Targeted Recovery Manager Gate

## Decision

**CANADA TARGETED RECOVERY MANAGER GATE — PASS**

**RECOMMENDATION B — REBUILD CANADA**

**NEXT AUTHORIZED STAGE: Canada Rebuild Admission Policy Gate — READ-ONLY**

This is a manager decision only. It authorizes no rebuild, admission, integration, mapping, eligibility work or Universe write.

## Start and authorized stage

- Repository: `akx0801-hub/welt-swing-long-data`
- Branch: `main`
- Start HEAD: `4828aa769d821f5b12f4f5c81e1b7f7a9e77bb48`
- Starting commit: `Canada targeted manual identity recovery`
- Authorized stage: Canada Targeted Recovery Manager Gate — READ-ONLY
- Research Partial: 2527
- Strict: 759
- Frozen: 0

## Verified evidence history

| Stage | Result |
|---|---|
| Canada Conversion / Identity Gate | 217 baseline rows; 0 conversion-ready; 217 identity review |
| Canada Exact Evidence Acquisition v1 | No conversion-ready Canada output |
| Canada Source Qualification Gate | Source stack only partially qualified |
| Canada Exact Evidence Acquisition v2 | 0 EVIDENCE_READY / 217 reviewed |
| Targeted Manual Identity Recovery | 30 selected and reviewed; 0 RECOVERY_READY / 30 RECOVERY_REVIEW |

The most recent 30-row sidecar is a complete bounded result for the selected scope. It reports 0 verified ISINs, 0 verified Share Classes and 0 verified Instrument Types; only the existing XTSE and ticker context was verified.

## Meaning of 0/30

The result does not prove that all 217 historical rows are wrong, that the issuers do not exist, or that TSX data is unusable. It shows that the legacy Membership could not be converted into reproducible Security-level identity under the enforced rules, even for an objectively selected subset intended to favor simpler cases.

The required identity remains:

`ISIN + Primary_MIC + Primary_Ticker`

and must describe the same concrete Security and Share Class. Ticker-only, CUSIP-only, issuer-level and silent Share-Class matches remain invalid.

A second targeted recovery batch is rejected. The evidence record is 0/217 in v2 and 0/30 in the targeted test, with HIGH manual cost and LIMITED scalability. Extending the same legacy-recovery method would therefore have poor expected value.

## Option A — Park Canada

Parking is operationally safe. It would preserve the 217 historical Membership rows unchanged and prevent further identity risk or expenditure.

However, it leaves Canada as unresolved historical baggage and does not test whether a clean, current-source population can deliver the missing identity fields. Canada has meaningful architecture value as a developed, non-US North American market with resources, energy, financials, industrials, utilities and other sectors. The current integrated balance is US-1/US-2: 741 rows and AU-1: 153 rows. A properly built Canada population could improve regional breadth.

Option A is therefore rejected as the immediate strategic priority, but the 217 legacy rows remain parked and untouched during any future work.

## Option B — Rebuild Canada

A clean rebuild is preferable to further repair of the legacy Membership because:

- the full v2 run yielded 0/217 ready identities;
- the targeted test yielded 0/30 ready identities;
- no ISIN, Share Class or Instrument Type was verified in either result;
- the existing lineage supports historical listing context but not a scalable Security-level identity base;
- manual recovery cost is HIGH and scalability is LIMITED;
- a new current-source pipeline can make exact identity, instrument classification, corporate-action QA and collision QA admission prerequisites from the start.

The next authorized step is only a **Canada Rebuild Admission Policy Gate — READ-ONLY**. That later policy gate must decide the source universe, source hierarchy, instrument policy, current-listing rules, identity fields, collision rules and admission gates. This report does not choose TSX Composite, TSX 60, TSX Completion, ETF holdings, a target count or any concrete candidate population.

## Governance requirements for any later rebuild

- The 217 legacy Canada rows remain unchanged.
- No deletion, replacement, renumbering, silent migration or automatic remapping.
- New candidate/admission artifacts must be separate from the legacy Membership.
- Identity must remain exact Security + Share Class + `ISIN + Primary_MIC + Primary_Ticker`.
- ISIN format and check digit must be validated.
- TSX and TSX Venture must be distinguished by evidence.
- Corporate actions and current listing status must be checked.
- Collision QA must be run against Research Partial.
- Ambiguous cases remain fail-closed.
- No CUSIP-only, ticker-only or issuer-level fallback.
- A later separate Manager/Integration Gate is required before any Universe write.
- Alpha Vantage remains prohibited.

## Strategic value and opportunity cost

Canada is strategically relevant for regional diversification, but the legacy-recovery route is not economically justified after two negative tests. Rebuild is a cleaner architecture decision than continuing to spend effort on an identity-poor historical list.

Korea, AU-2, US-3 and other populations are considered only as opportunity-cost context. None is started or authorized by this report. The sole authorized next step is the Canada Rebuild Admission Policy Gate.

## Final recommendation

**CANADA TARGETED RECOVERY MANAGER GATE — PASS**

**RECOMMENDATION B — REBUILD CANADA**

**NEXT AUTHORIZED STAGE: Canada Rebuild Admission Policy Gate — READ-ONLY**

The legacy Canada Membership is **UNCHANGED**. This report authorizes no Canada rebuild itself, no admission, no mapping, no integration and no data write.

## Quality gates

- G0 Correct `origin/main` HEAD: PASS
- G1 Correct authorized manager stage: PASS
- G2 Full Canada baseline 217 verified: PASS
- G3 Full Evidence v2 result acknowledged: PASS
- G4 Targeted Recovery 30-row result acknowledged: PASS
- G5 0 RECOVERY_READY acknowledged: PASS
- G6 Manual Cost HIGH acknowledged: PASS
- G7 Scalability LIMITED acknowledged: PASS
- G8 Second recovery batch rejected: PASS
- G9 Park option evaluated: PASS
- G10 Rebuild option evaluated: PASS
- G11 Governance implications evaluated: PASS
- G12 Strategic Canada value evaluated: PASS
- G13 Opportunity cost evaluated: PASS
- G14 Exactly one recommendation selected: PASS
- G15 Exact next stage defined: PASS
- G16 No Universe/Data write: PASS
- G17 No follow-on stage executed: PASS

## No-touch confirmation

The Canada Membership, Research Partial, Strict, Frozen, Universe/Data Master, History, Liquidity, Eligibility, Scan/U3K and Welt-Swing v7.2 remain unchanged. No second recovery batch, rebuild, admission or other population was started.

