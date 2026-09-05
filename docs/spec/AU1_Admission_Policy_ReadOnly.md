# AU-1 Admission Policy (Read-Only)
START 386af4c. NO DOWNLOAD. NO BUILD. NO CANDIDATE LIST.
READY != BUILD AUTHORIZATION.
## Scope
S&P/ASX 200 Ordinary on XASX. Expansion, AU membership 0. Not ASX-full, not History.
## Evidence
R1 official S&P/ASX 200. R2 ASX/ASIC. R3 institutional index fund (no override of R1/R2). R4 Wikipedia never sole ADMIT.
Discovery != admission evidence.
## Identity
Mandatory ISIN + XASX + ticker. AUD required. No ticker-only. No ISIN fallback.
WS_ID later WS:XASX:TICKER. No overwrite.
## Instruments
Ordinary: ADMIT candidate. A-REIT: REVIEW. Stapled: REVIEW (stapled != common).
ETF/Fund: EXCLUDE. Preferred: DISCOVER. Other units: EXCLUDE. CDI/DR: EXCLUDE.
Foreign-incorp ASX ordinary: REVIEW (do not copy US-2 foreign-ISIN ADMIT).
## Dual / MIC
XASX only. No MIC-merge. Ticker collision other MIC allowed if identity differs.
## Buckets
DISCOVERY sidecar. ADMIT ordinary+XASX+ISIN+AUD+R1orR3. REVIEW REIT/stapled/identity. EXCLUDE ETF/CDI.
## Reuse / do not copy
Reuse: sidecar, buckets, identity triple, write-gate, fail-closed.
Do not copy: US REIT-as-afterthought, US foreign-ISIN ADMIT, US dual MIC.
## D1-D9
D1 YES. D2 XASX YES. D3 ordinary YES. D4 A-REIT REVIEW. D5 stapled REVIEW.
D6 ETF EXCLUDE. D7 CDI EXCLUDE. D8 ISIN+XASX+TICKER. D9 READY WITH CONDITIONS.
Conditions: separate manager order; R1 or R3; no Wikipedia-only; no REIT/stapled ADMIT.
## Gate
POLICY -> Manager -> Admission Build -> Evidence -> Manager -> Write -> Audit -> STOP.
AU-1 ADMISSION POLICY — READ-ONLY COMPLETE
NEXT ACTION: STOP — MANAGER GATE REQUIRED FOR AU-1 ADMISSION BUILD
