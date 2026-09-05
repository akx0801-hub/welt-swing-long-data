# P4 Composition & Coverage Audit — 759 Strict Candidates

**HEAD Ausgang:** `11d7885`  
**Modus:** DEV / RESEARCH / SHADOW — nicht produktiv  
**Run:** READ-ONLY. Universe_Write=NO. Eligibility unverändert. Frozen U3K=0.  
**Strict:** 759 (Invariant = 759)

---

## Executive Summary

Die 759 sind **kein Welt-U3K**. Sie sind die Schnittmenge aus:

1. **585 COMMON_STOCK / UNMAPPED** aus v0.38-History — Index-Scheiben Asia (CSI300, Nikkei, TW50, Nifty).
2. **137 EVIDENCE_CANDIDATE_APPLIED** aus der v0.42–v0.50-Welle (STOXX600-Ordinary, History v0.47) — 10 der alten 147 sind REVIEW und nicht in den 759.
3. **37 YFINANCE_VERIFIED** BVMF Ordinary (Brazil IBRX).

**US-Primary (XNYS/XNAS): 0.**  
**Share_Class leer: 291.** Das sind keine Ordinary-Evidence.

OBSERVATION ≠ ERROR. Die Konzentration folgt den Index-Tags des Research-Partial, nicht einem Scan-Fehler.

---

## 4.1 MIC / Exchange

| MIC | n | % | Region-Map (closed, not domicile) |
|---|---|---|---|
| XTKS | 197 | 26.0 | Asia-Pacific |
| XSHG | 186 | 24.5 | Asia-Pacific |
| XSHE | 108 | 14.2 | Asia-Pacific |
| XTAI | 49 | 6.5 | Asia-Pacific |
| XNSE | 45 | 5.9 | Asia-Pacific |
| XETR | 39 | 5.1 | Europe |
| BVMF | 37 | 4.9 | Americas |
| XPAR | 35 | 4.6 | Europe |
| XSTO | 18 | 2.4 | Europe |
| XMIL | 13 | 1.7 | Europe |
| XLON | 8 | 1.1 | Europe |
| XCSE | 7 | 0.9 | Europe |
| XAMS | 5 | 0.7 | Europe |
| XWBO | 4 | 0.5 | Europe |
| XDUB | 3 | 0.4 | Europe |
| XMAD | 2 | 0.3 | Europe |
| XBRU | 1 | 0.1 | Europe |
| XHEL | 1 | 0.1 | Europe |
| XWAR | 1 | 0.1 | Europe |

Region-Map (MIC, nicht Emittenten-Sitz): Asia-Pacific 585 (77.1%) · Europe 137 (18.1%) · Americas 37 (4.9%) · US-MIC 0.

Top-3 MIC XTKS/XSHG/XSHE = 491 (64.7%).

## 4.2 Country (Universe-Feld) und ISIN-Prefix

Country ist das vorhandene Universe-Feld. Nicht an ISIN angeglichen, nicht geraten.

| Country | n | % |
|---|---|---|
| China | 294 | 38.7 |
| Japan | 197 | 26.0 |
| Taiwan | 49 | 6.5 |
| India | 45 | 5.9 |
| DE | 39 | 5.1 |
| Brazil | 37 | 4.9 |
| FR | 35 | 4.6 |
| SE | 18 | 2.4 |
| IT | 13 | 1.7 |
| GB | 9 | 1.2 |
| DK | 7 | 0.9 |
| NL | 4 | 0.5 |
| AT | 4 | 0.5 |
| IE | 3 | 0.4 |
| ES | 2 | 0.3 |
| BE | 1 | 0.1 |
| FI | 1 | 0.1 |
| PL | 1 | 0.1 |

ISIN-Prefix (erste zwei Zeichen, keine Sitz-Behauptung):

| ISIN_Prefix | n | % |
|---|---|---|
| XX | 668 | 88.0 |
| IN | 45 | 5.9 |
| TW | 43 | 5.7 |
| KY | 3 | 0.4 |

Primary_Universe_Index:

| Index | n | % |
|---|---|---|
| CN_CSI300 | 294 | 38.7 |
| JP_N225 | 197 | 26.0 |
| EU_STOXX600 | 137 | 18.1 |
| TW_TW50 | 49 | 6.5 |
| IN_NIFTY50 | 45 | 5.9 |
| BR_IBRX100 | 37 | 4.9 |

## 4.3 Instrument_Type

| Instrument_Type | n | % |
|---|---|---|
| COMMON_STOCK | 585 | 77.1 |
| ORDINARY_SHARE | 174 | 22.9 |

UNKNOWN in Strict: **0**. Keine Reklassifikation.

## 4.4 Share_Class

Leere Felder **nicht** als Ordinary gelesen.

| Bucket | n | % |
|---|---|---|
| ORDINARY_OR_COMMON_EVIDENCE | 465 | 61.3 |
| MISSING_EMPTY | 291 | 38.3 |
| OTHER | 3 | 0.4 |

Empty/missing raw Share_Class: **291**. A_SHARE ist China-A-Evidence, nicht v0.42-Verified_Share_Class.

## 4.5 Liquidity / Turnover

Schwellen unverändert. Bänder nur Reporting.

| Liquidity_Class | n | % |
|---|---|---|
| PREFERRED | 695 | 91.6 |
| STANDARD | 64 | 8.4 |

Turnover-Bänder MedianTurnover20_EUR: 15–20m · 20–50m · 50–100m · ≥100m.

| Band | n | % |
|---|---|---|
| 15-20m | 64 | 8.4 |
| 20-50m | 237 | 31.2 |
| 50-100m | 185 | 24.4 |
| >=100m | 273 | 36.0 |

PREFERRED-Klasse = ≥20m: 695. STANDARD 15–20m: 64. Kein Strict unter 15m.

## 4.6 Mapping_Status

UNMAPPED ≠ kein Yahoo. Keine Remediation.

| Mapping_Status | n | % |
|---|---|---|
| UNMAPPED | 585 | 77.1 |
| EVIDENCE_CANDIDATE_APPLIED | 137 | 18.1 |
| YFINANCE_VERIFIED | 37 | 4.9 |

## 4.7 History Source

Kein Re-Download.

| History_Source | n | % |
|---|---|---|
| v0.38 | 622 | 81.9 |
| v0.47 | 137 | 18.1 |

v0.38 deckt die Asia-COMMON-Scheibe. v0.47 die 137 Evidence-Ordinary.

## 4.8 Overlap 147 → 759

| | n |
|---|---|
| 147 in 759 | 137 |
| 147 nicht in 759 | 10 |
| neu in 759 (nicht in 147) | 622 |

Drop-Grund der 10: {'INSTRUMENT_REVIEW': 10} — alle `INSTRUMENT_REVIEW` (P1 fail-closed). Nicht auf 147 zurückbiegen.

Strukturelle Erklärung 147→759: 147 war die **liquide Ordinary-Teilmenge der 239-Welle**. 759 = diese 137 plus 585 v0.38-COMMON (Asia-Indizes) plus 37 BVMF Ordinary. Andere Gates, andere Coverage.

## 5. Antworten

1. **MIC-Konzentration:** Ja. XTKS+XSHG+XSHE = 491 (64.7%).
2. **Region:** Asia-Pacific dominant, Europa = STOXX-Welle, Americas = nur BVMF, US-Primary 0.
3. **COMMON vs ORDINARY:** 585 / 174.
4. **Share_Class leer:** 291.
5. **UNMAPPED:** 585.
6. **Cluster:** Pipeline-Wellen = Index-Scheiben. Kein Zufall.
7. **147→759:** siehe 4.8. Nicht Fehler.
8. **Namens-Duplikate in 759:** 0 (exakter Name). Multi-Class-Paare Pref/Ord liegen **nicht** beide in Strict (Pref ist nicht Strict).
9. **Coverage-Lücken (Beobachtung):** US 0; UK/XLON nur 8; Pref-Ordinary-Löcher DE; 15 REVIEW nicht in Strict; Dual-Listings nicht gemerged.
10. **Observation vs Action:** Konzentration und 147→759 sind **Observation**. Potenzieller späterer Bedarf (nicht dieser Auftrag): US-Coverage, Canonical-Policy, REVIEW-Fälle, Pref-Ordinary-Loch. Kein Error-Fix in P4.

---

## Anhänge (sichtbar, unapplied)

### 6A — 15 REVIEW

Siehe `appendix_6A_review_15.csv`. Alle Instrument_Type=UNKNOWN, Eligibility nicht Strict. Keine Reklassifikation.

### 6B — Pref-only

Siehe `appendix_6B_pref_only.csv`. Ordinary_In_1633=NO bedeutet Coverage-Loch, nicht Scan-Default Preferred.

### 6C — Dual-Listing

Siehe `appendix_6C_dual_listing.csv`. Kein Merge über MIC.

---

## 671 UNKNOWN

Instrument_Type=UNKNOWN im Master 1633: **686** (Kontext).  
Davon 15 HOLD_REVIEW mit Share-Class-Evidence; Rest ohne Closed-Map-Apply.  

**Nicht segmentiert, nicht sampled, nicht remediat.** Separater Auftrag.

---

## Canonical Scan Policy — DRAFT, unapplied

Discovery: alle bekannten Klassen bleiben.  
Scan: eine kanonische Ordinary/Common je Emittent × Primärmarkt.  
Preferred: nie Scan-Default.  
Unit/SDB/DR: kein Scan-Default.  
Dual-Listing: kein Merge über MIC; je Markt eigene Identität.  
Execution getrennt.

Nicht bindend. Kein Universe-Write. Keine Eligibility-Regel. P5 braucht Extra-Auftrag.

---

## Invarianten

```
strict = 759
universe_write = false
eligibility_promoted = false
u3k_frozen_members = 0
productive = false
unknown_remediation = false
```

P4 STOPP. Kein Freeze. Kein Folgeauftrag aus diesem Report.
