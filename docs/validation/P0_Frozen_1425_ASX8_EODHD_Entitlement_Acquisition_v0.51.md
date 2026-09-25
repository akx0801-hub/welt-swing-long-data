# P0 Frozen-1425 ASX-8 EODHD Entitlement Precheck and Conditional Exact-Date Acquisition v0.51

## Gate verdict

**PASS_WITH_ACCESS_BLOCKED**

Required start HEAD: `24a59c988de4b7183877b456109d00c4833fde7d`.

The required start HEAD was verified against live `main` before the write stage and was identical. v0.50 was validated before this gate: `PASS_WITH_ACCESS_BLOCKED`, 18/18 validation checks PASS, Frozen 1425, READY 1417, QUARANTINE 8, P0_PRICE_CACHE_READY = NO. Runtime authority remains v0.48 with SQLite SHA-256 `8973ff393db23c7e2d456502c2a71f085f17407dc5ed244dcc04d566c87d4063`.

No runtime cache, Frozen membership, provider mapping, QA contract or productive state was mutated.

## Phase A — credential/access precheck

**CREDENTIAL_AVAILABLE = NOT_VERIFIABLE**

Repository and workflow search found no committed EODHD integration, no approved EODHD environment-variable/secret contract and no existing workflow reference to an EODHD credential. The connected GitHub interface does not expose GitHub Actions secret values or the sensitive secrets API. This gate therefore does not invent a secret name and does not probe unrelated secrets.

The previous v0.50 evidence stated that no entitled EODHD token was connected at that time. That is historical evidence only and is not promoted to a current proof of absence.

No credential value was printed, persisted, logged, hashed, transformed or otherwise exposed.

## Access-rights precheck

Current public EODHD documentation establishes the following product capability:

- EOD Historical Data API returns date/open/high/low/close/adjusted_close/volume.
- Tickers use `SYMBOL.EXCHANGE`.
- Free-plan historical EOD access is limited to the past year; older history requires paid entitlement.
- Public self-service/personal plans are for personal use; commercial/professional use requires separate licensing.
- Non-professional terms permit private storage/manipulation/analysis but prohibit redistribution.

The actual account/plan/entitlement available to this project is not identifiable from the authorized execution environment.

The repository is currently public. Therefore raw licensed EODHD values must not be committed here absent explicit redistribution/public-repository permission.

| Right | Result | Basis |
|---|---|---|
| API_ACCESS_ALLOWED | NOT_VERIFIED | No usable credential/plan can be established. |
| INTERNAL_RUNTIME_USE_ALLOWED | NOT_VERIFIED | Actual use class/entitlement is not identified. |
| RAW_REPOSITORY_PERSISTENCE_ALLOWED | NO | Public repository plus no explicit redistribution/public-Git permission established; fail closed. |
| REDISTRIBUTION_ALLOWED | NOT_VERIFIED | Public personal terms prohibit redistribution; no applicable commercial entitlement was identified. |

Product capability for 2024-11-15 is documented, but **actual entitlement to that depth is NOT_VERIFIED**.

## Phase-A hard gate

Critical conditions:

- credential usable: **NOT_VERIFIED**
- historical ASX EOD endpoint accessible under actual entitlement: **NOT_VERIFIED**
- target-date entitlement: **NOT_VERIFIED**
- exact eight-security request scope technically possible: **YES**
- internal analytical/runtime use permitted: **NOT_VERIFIED**

Therefore:

**ACQUISITION_AUTHORIZED = NO**

Per the gate, acquisition stopped here. No EODHD market-data API request was made.

## Provider-specific identity

Provider identity metadata only; canonical project mappings remain unchanged.

| Canonical Security | Existing project identity | EODHD request identity | Identity status |
|---|---|---|---|
| ANZ | WS:XASX:ANZ / ANZ.AX | ANZ.AU | VERIFIED |
| BSL | WS:XASX:BSL / BSL.AX | BSL.AU | VERIFIED |
| BXB | WS:XASX:BXB / BXB.AX | BXB.AU | VERIFIED |
| CBA | WS:XASX:CBA / CBA.AX | CBA.AU | VERIFIED |
| NXT | WS:XASX:NXT / NXT.AX | NXT.AU | VERIFIED |
| PME | WS:XASX:PME / PME.AX | PME.AU | VERIFIED |
| QAN | WS:XASX:QAN / QAN.AX | QAN.AU | VERIFIED |
| SDF | WS:XASX:SDF / SDF.AX | SDF.AU | VERIFIED |

The EODHD public financial-summary pages resolve all eight `.AU` identifiers to the corresponding Australian issuers. EODHD documentation states that its market-data identifiers use the provider exchange-code suffix rather than the MIC. No canonical `Primary_Ticker`, `Primary_MIC`, `Source_WS_ID`, `Security_Key` or Yahoo mapping was modified.

## Conditional acquisition result

**NOT RUN — PHASE A DID NOT PASS.**

- EODHD market-data API calls: 0
- Yahoo/yfinance calls: 0
- Alpha Vantage calls: 0
- Scalable calls: 0
- Licensed complete OHLC rows acquired: 0
- Licensed raw EODHD values persisted: 0
- Cross-source field comparison: NOT RUN
- PME EODHD control comparison: NOT RUN

The pre-existing v0.49/v0.50 PME, CBA and QAN evidence remains historical project evidence only and was not re-acquired or rewritten in this gate.

## Per-security authority verdict

All eight remain **ACCESS_BLOCKED** for this gate because entitlement/runtime-use authorization is not verified and no EODHD market-data request was authorized.

CACHE_REWRITE_EVIDENCE_READY = **NO** for all eight.

## Runtime / semantic state

Unchanged:

- Frozen: 1425
- READY: 1417
- QUARANTINE: 8
- P0_PRICE_CACHE_READY = NO
- Runtime authority: v0.48
- Runtime SQLite SHA-256: `8973ff393db23c7e2d456502c2a71f085f17407dc5ed244dcc04d566c87d4063`
- cache mutation: false
- Frozen mutation: false
- provider mapping mutation: false
- P0: NOT RUN
- features: NOT RUN / NOT PROMOTED
- RS: NOT RUN / NOT PROMOTED
- parameters: NOT PROMOTED
- productive: false

## Public evidence consulted during precheck

- EODHD End-of-Day Historical Data API: https://eodhd.com/financial-apis/api-for-historical-data-and-volumes
- EODHD Exchanges API: https://eodhd.com/financial-apis/exchanges-api-list-of-tickers-and-trading-hours
- EODHD Commercial vs Personal licence use: https://eodhd.com/financial-apis/commercial-vs-personal-license-use
- EODHD Terms and Conditions: https://eodhd.com/financial-apis/terms-conditions
- Provider identity pages: https://eodhd.com/financial-summary/{ANZ,BSL,BXB,CBA,NXT,PME,QAN,SDF}.AU

These were documentation/identity page reads only, not EODHD market-data API acquisition calls.

## Next gate

**P0 ASX OHLC SOURCE-POLICY / QA-CONTRACT DECISION GATE**

Do not execute automatically.

## Hard stop

STOP after persistence of this entitlement/access evidence.

No subscription purchase. No account creation. No cache rewrite. No READY promotion. No P0. No features. No RS. No parameter promotion. No Universe mutation. No trading.
