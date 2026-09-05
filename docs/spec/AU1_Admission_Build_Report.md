# AU-1 S&P/ASX 200 Admission Build Report
1. Start HEAD: ffdffef. SIDECAR ONLY. NO UNIVERSE WRITE.
2. Source: iShares Core S&P/ASX 200 ETF (IOZ), BlackRock product 251852, XLS holdings. Evidence rank 3 institutional named-index file. Wikipedia not used. CSV ajax rejected (no ISIN).
3. Snapshot date: 03-Sept-2026
4. Discovery: 201 IOZ equity holdings tagged SP_ASX_200. Nominal index 200 is not an ADMIT target.
5. ADMIT: 159 ordinary AU-ISIN XASX AUD.
6. REVIEW: 31 = A-REIT 20 + stapled-non-RE 3 + foreign-ordinary NZ 8.
7. EXCLUDE file: 16 = CDI 11 + non-index cash/futures 5. Discovery EXCLUDE (in 201): 11 CDI. Reconciliation: Discovery 201 = ADMIT 159 + REVIEW 31 + Discovery-EXCLUDE 11. Non-index holdings are outside Discovery by classification model.
8. Instrument: ADMIT Instrument_Type=ORDINARY only. Preferred/hybrid/units/ETF in ADMIT = 0. A-REIT and stapled never ADMIT.
9. Identity QA: all ADMIT have ISIN+XASX+ticker. Missing ISIN ADMIT=0. Duplicate WS_ID Discovery=0. Duplicate ISIN Discovery=0. No ticker-only ADMIT.
10. MIC QA: all Discovery and all ADMIT MIC=XASX. No MIC-merge. No US/CA/KR/HK in Discovery.
11. Existing-universe overlap vs Research Partial 2374: identity triple = 0. ISIN overlap = 0. Ticker-only collisions ALLOWED (21): ALK,ALL,AMP,ASB,BEN,CAR,CSL,ELD,ELV,EMR,HLI,IAG,NEM,NEU,NXT,ORA,ORI,RMD,RSG,VNT,XYZ.
12. Evidence QA: all Discovery Evidence_Source=iShares_IOZ, Rank=3, Snapshot=03-Sept-2026. Rank 1 official S&P file not used (unavailable this build). Rank 4 Wikipedia not used for ADMIT.
13. A-REIT: fail-closed REVIEW when Sector=Real Estate or name contains REIT. Count 20. ADMIT A-REIT = 0. Not reinterpreted as ordinary.
14. Stapled: fail-closed REVIEW when name has STAPLED / GROUP UNITS / trailing UNITS, unless already A-REIT. Non-REIT stapled: 3. ADMIT stapled = 0. Stapled != common.
15. CDI: EXCLUDE when issuer name contains CDI. Count 11. Not converted to ordinary XASX ADMIT.
16. ETF/Fund: EXCLUDE policy. ETF in IOZ equity holdings = 0. Cash/futures EXCLUDE as NON_INDEX_HOLDING.
17. Exceptions: ADMIT < 200 by design (policy-compliant, not maximization). Foreign-incorp ASX ordinary (NZ ISIN) = REVIEW, do not copy US-2 foreign-ISIN ADMIT. PXA PEXA GROUP LTD is Real Estate sector so REVIEW_AREIT fail-closed (not auto-ordinary). MQG name contains DEF in IOZ source; left as ordinary ADMIT (source Asset Class Equity, AU ISIN, not CDI/REIT/stapled).
18. Gates G0-G16: {'G0': 'PASS', 'G1': 'PASS', 'G2': 'PASS', 'G3': 'PASS', 'G4': 'PASS', 'G5': 'PASS', 'G6': 'PASS', 'G7': 'PASS', 'G8': 'PASS', 'G9': 'PASS', 'G10': 'PASS', 'G11': 'PASS', 'G12': 'PASS', 'G13': 'PASS', 'G14': 'PASS', 'G15': 'PASS', 'G16': 'PASS'}
19. Final build status: AU-1 S&P/ASX 200 COMMON — ADMISSION BUILD PASS. Research Partial 2374 unchanged. US-1 372 unchanged. US-2 369 unchanged. Strict 759 unchanged. Frozen 0 unchanged. AU membership in Research Partial = 0. universe_write=false.
20. Next manager gate: SEPARATE AU-1 EVIDENCE / ADMISSION GATE. ADMIT != INTEGRATED. BUILD PASS != WRITE AUTHORIZATION. No History / Liquidity / Eligibility / Korea / US-3 / Canada.
