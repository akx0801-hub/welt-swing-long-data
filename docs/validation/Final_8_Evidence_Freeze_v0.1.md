# Welt-Swing Long DEV — Final 8 Evidence Freeze v0.1

**Input:** Final Remediation v0.3  
**Master:** 3,664 rows  
**Active rows:** 3,663  
**Open review rows before freeze:** 8  
**Price/OHLCV:** off  
**P0:** off  
**Alpha Vantage:** forbidden  
**Productive authority:** no

## Purpose

This freeze closes the eight provider-symbol gaps left after v0.3 using explicit
public evidence. It is deliberately separate from the price pipeline.

The freeze does not alter canonical `WS_ID` values. It only freezes an explicit
provider symbol for each of the eight review rows and records the evidence URL
and rationale in the master.

## Frozen mappings

| Security | Source / old candidate | Frozen provider symbol | Evidence basis |
|---|---|---|---|
| AUTO1 Group | AG1G.DE / AG1.DE | `AG1.DE` | AUTO1 IR ticker AG1 + Yahoo provider page |
| Amadeus IT Group | AMA.MC / AMS.MC | `AMS.MC` | Amadeus annual accounts ticker AMS + Yahoo provider page |
| Epiroc A | EPIRa.ST / EPIR-A.ST | `EPI-A.ST` | **Candidate corrected**: Epiroc official ticker EPI A + Yahoo provider page |
| Ericsson B | ERICb.ST / ERIC-B.ST | `ERIC-B.ST` | Ericsson official Nasdaq Stockholm ticker ERIC B + Yahoo provider page |
| Hexagon B | HEXAb.ST / HEXA-B.ST | `HEXA-B.ST` | Hexagon IR ticker HEXA B + Yahoo provider page |
| Roche participation certificate | ROPC.S / ROG.SW | `ROP.SW` | **Corporate-action correction**: ROG ended 16 Mar 2026; ROP began 17 Mar 2026 + Yahoo provider page |
| Swiss Re | SRENH.S / SREN.SW | `SREN.SW` | Swiss Re SIX ticker SREN + Yahoo provider page |
| ALFA | ALFA A / ALFAA.MX | `ALFAA.MX` | BMV ticker ALFA A + public market identifier evidence for ALFAA.MX |

## Important corrections

### Epiroc

The v0.3 candidate `EPIR-A.ST` was not the Yahoo symbol. Epiroc's official
Nasdaq Stockholm ticker is `EPI A`, and Yahoo exposes the A share as
`EPI-A.ST`.

### Roche

`ROG.SW` must not be frozen. Roche's old non-voting security `ROG` had its last
SIX trading day on 16 March 2026. The replacement participation certificate
started trading on 17 March 2026 under ticker `ROP`, ISIN `CH1499059983`.
Yahoo exposes the current instrument as `ROP.SW`.

### ALFA

Yahoo Search did not return the exact provider symbol in the v0.3 run. The
freeze therefore uses explicit public-market evidence instead of pretending the
search succeeded: BMV notation is `ALFA A`, and public identifier evidence maps
the Mexican listing to `ALFAA.MX`.

## Outputs

- `universe/Welt-Swing-Universe-Master-EvidenceFrozen-v0.7.csv`
- `universe/Welt-Swing-Universe-Master-EvidenceFrozen-v0.7.xlsx`
- `output_identity_evidence_freeze/final_8_evidence_audit_v0.1.csv`
- `output_identity_evidence_freeze/summary_v0.1.json`

Successful freeze target:

- master rows: 3,664
- active rows: 3,663
- active provider mappings: 3,663
- active unresolved: 0
- active provider coverage: 100%

Even after this freeze, `price_run_allowed_after_this_step` remains `false`.
The next full price run must be released explicitly as a separate workflow step.
