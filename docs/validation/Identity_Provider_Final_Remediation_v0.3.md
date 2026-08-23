# Welt-Swing Long DEV — Identity Provider Final Remediation v0.3

**Input:** v0.5 remediated master, 3.664 rows  
**Target:** exactly the 121 review rows left by v0.2  
**Price/OHLCV:** off  
**P0:** off  
**Alpha Vantage:** forbidden  
**Productive authority:** no

## Purpose

v0.3 is a bounded final provider-symbol remediation. It does not reopen the
whole universe and it does not run price history. Every one of the 121 v0.2
review rows must be explicitly covered by either:

1. a curated provider-symbol candidate that is validated at runtime with
   Yahoo Search;
2. a narrowly documented public-reference exception; or
3. a stale/delisted source-member exclusion.

If the 121-row input changes, the workflow fails rather than silently applying
a mapping to a different universe.

## Market-specific corrections

The curated candidate layer covers Reuters/RIC/source mnemonics that are not
Yahoo symbols, including examples such as:

- BMWG.DE -> BMW.DE
- DB1Gn.DE -> DB1.DE
- VOWG_p.DE -> VOW3.DE
- LVMH.PA -> MC.PA
- CARL/Stockholm-style share classes -> `-A` / `-B` Yahoo notation
- GFNORTE O -> GFNORTEO.MX
- JSE source names -> local `.JO` symbols

These are candidates only. Normal rows are promoted only when Yahoo Search
returns the exact equity symbol.

## Public-reference exceptions

A small set is separately supported by current public/issuer evidence. Examples:

- Arcadis: `ARCAD.AS` on Yahoo Finance.
- Helvetia Baloise: issuer confirms SIX ticker `HBAN`; Yahoo uses `HBAN.SW`.
- Octave Intelligence: issuer/Nasdaq confirm Stockholm `OCTV SDB` represents
  one underlying Class B share; the regular Nasdaq Class B ticker is `OCTV`.
  Because a stable Yahoo Stockholm SDR symbol is not observed, v0.3 records
  `OCTV` as an **alternate 1:1 underlying provider mapping**, never as the
  Stockholm primary symbol.
- Several JSE codes are independently corroborated by public JSE/market
  references.

## Stale source member

MultiChoice is not assigned a fabricated live mapping. Current public sources
indicate the security was taken over/delisted. v0.3 marks that source row
inactive and excludes it from the active provider-coverage denominator.

This does not claim that the old Wikipedia-derived JSE source list is a current
exact Top-40 membership file. JSE membership freshness remains a separate
universe-governance issue.

## Outputs

- `universe/Welt-Swing-Universe-Master-FinalMapped-v0.6.csv`
- `universe/Welt-Swing-Universe-Master-FinalMapped-v0.6.xlsx`
- `output_identity_final/summary_v0.3.json`
- `output_identity_final/final_remediation_audit_v0.3.csv`
- `output_identity_final/review_queue_v0.3.csv`
- `output_identity_final/promotion_overrides_v0.3.csv`
- `output_identity_final/stale_exclusions_v0.3.csv`

The production override registry is deliberately not edited automatically.
After the result is inspected, verified promotions can be frozen into the
provider mapping layer.

Even if the coverage-ready flag becomes true, the workflow keeps
`price_run_allowed_after_this_step=false`; release of a full price run is a
separate explicit decision.
