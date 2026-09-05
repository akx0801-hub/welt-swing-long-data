# WELT-SWING CURRENT HANDOFF – v0.50

Stand: 2026-09-05
HEAD (Ausgangspunkt): bcf9f89 — v0.50 research candidate list 147 sidecar no u3k freeze
Repo: https://github.com/akx0801-hub/welt-swing-long-data
Modus: DEV / RESEARCH / SHADOW — nicht produktiv
Arbeit nach Review: P0 Doku → P1 Instrument_Type → P2 History/Liquidity + Eligibility-Dry-Run
Spec: docs/spec/WELT-SWING-LONG-DEV-v0.1-MASTER-2026-08-23.md
Produktive Trading-Autorität: Welt-Swing v7.2

Ersetzt den veralteten CURRENT-Handoff.md (v0.19).

## 1. System
Free-Data-Engine für Strict-Universe (U3K, Ziel \~3000 liquide Primary-Listings).
Pfad: Identity → Yahoo-Mapping → yfinance → gitignored SQLite → QA → MedianTurnover20_EUR → Eligibility.
Verboten ohne Extra-Freigabe: Alpha Vantage, U3K-Freeze, produktiver P0, FULL_SCAN, v7.2-Übernahme, Identity-Mutation.

## 2. Master 1633 (Research Partial)
universe/research_partial_1633.csv
Universe_Status=ACTIVE_VERIFIED = Membership, nicht Eligibility.

Mapping: UNMAPPED 1296 | EVIDENCE_CANDIDATE_APPLIED 239 | YFINANCE_VERIFIED 79 | NOT_VERIFIED 19
UNMAPPED heißt nicht „kein Yahoo“ — in v0.38 oft MAPPING_DATA_CONFIRMED. Kein blinder Re-Download.
239 Applied = 1:1 die v0.38 mapping_remediation_queue.
SWING_U3K_FROZEN_v0.5.csv = Header, 0 Members. Bleibt so.

Instrument vor P1: COMMON_STOCK 625 · UNKNOWN 910 · ORDINARY_SHARE 79 · PREFERRED_SHARE 12 · UNIT 7
Die 239 Applied waren UNKNOWN. Share-Class nur in config/mapping_evidence_acquisition_v0.42.csv.

## 3. v0.42–v0.50 (239-Welle)
Nicht „Europa = U3K“, sondern die Lücke MAPPING_DOWNLOAD_NO_DATA.

v0.42 Evidence HIGH 239/239
v0.43 Probe 239 PASS (18× XLON GBp)
v0.44 Apply nur Yahoo_Symbol + Mapping_Status
v0.47 History 236 PASS, 3 zu kurz (MICC.AS AMV0.DE OCTV-SDB.ST)
v0.48 Liquidity 125 / 27 / 69 / 15; XLON Scale 0.01
v0.49 Dry-Run Universe_Write=NO
v0.50 Liste 147 Research Candidates

147 ≠ U3K. Teilmenge der 239 innerhalb der 1633.
v0.49-Ausschlüsse: 69 Exception · 15 Fail-Liq · 5 Pref/PS (HEN3 PAH3 SRT3 VOW3 ROP.SW) · 3 Parks.
Zwei Caches: v0.38 (1365) vs. applied_239 sqlite (gitignored). Merge = P2, kein Voll-Download.

## 4. v0.38 Rest
PASS_HISTORY 1365 · Quality fail 7 · Insufficient 3 · Instrument fail 19
Liquidity: Pref 925 · Std 89 · Low 268 · Fail 83 · Insufficient 268
Davon 664 PASS-History mit UNKNOWN — kein automatischer Strict-PASS.

## 5. Harte Regeln
Kein U3K-Freeze. Nicht produktiv. P2 Universe_Write=NO. Kein Alpha Vantage.
Identity frozen. Keine neue Mapping-Welle. UNKNOWN kein Strict-PASS. 147 ist nicht der U3K.

## 6. Arbeit nach v0.50
P0 Doku
P1 Closed-Map Share-Class → Type (nur 239 mit Evidence)
P2 WS_ID-Merge + Eligibility-Dry-Run, kein Universe-Write
671 UNKNOWN ohne Evidence: MISSING_EVIDENCE, nicht raten.
Nach P2 Stopp. Kein Freeze, kein 3663, keine 1296-Welle.

## 7. Invarianten
productive=false  p0=false  swing_u3k_frozen=false (0 members)
alpha_vantage=false  identity frozen  evidence csv frozen
sqlite not committed  eligibility_promoted=false
