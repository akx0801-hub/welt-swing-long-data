# WELT-SWING LONG DEV — Current-Master Universe Reconciliation & Freeze Plan v0.28

**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Stage:** `CURRENT_MASTER_OFFICIAL_SOURCE_UNIVERSE_RECONCILIATION_AND_FREEZE_PLAN`

## 1. Zweck

v0.28 beendet den Schwerpunkt auf der alten Phase2-/Pre-Master-Lineage und macht die aktuelle
**Current-Master Clean-Restart Lineage** wieder zum alleinigen primären Universe-Entwicklungsstrang.

Der Stage ist bewusst **offline-only**. Er lädt keine Constituents, keine Preise und keine News.

## 2. Autoritative Inputs

v0.28 pinnt:

- den DEV-Master `WELT-SWING LONG DEV v0.1`,
- `universe/Welt-Swing-Universe-Master-v2.0.xlsx`,
- den daraus erzeugten 1535er Research-Snapshot,
- dessen Manifest,
- die historische Research-1535-Price-Coverage nur als Kontext,
- v0.27 ausschließlich als Legacy-Closeout.

Die Phase2-/3663-Lineage besitzt **keine current-master-kanonische Source Authority**.

## 3. 14 Zielsegmente

Der Master fordert:

1. STOXX Europe 600
2. S&P Composite 1500
3. S&P/TSX Composite
4. S&P/BMV IPC
5. Nikkei 225
6. Hang Seng Index
7. CSI 300
8. Nifty 50
9. KOSPI 200
10. FTSE TWSE Taiwan 50
11. S&P/ASX 200
12. S&P/NZX 50
13. IBrX 100
14. FTSE/JSE Top 40

Der aktuelle r6-Master enthält sieben Segmente mit zusammen 1.535 Zeilen:

- EU_STOXX600 600
- CA_TSX 217
- JP_N225 225
- HK_HSI 93
- CN_CSI300 300
- IN_NIFTY50 50
- TW_TW50 50

Sieben Zielsegmente fehlen:

- US_SP1500
- MX_IPC
- KR_KOSPI200
- AU_ASX200
- NZ_NZX50
- BR_IBRX100
- ZA_TOP40

Für USA wird der bekannte harte Status erhalten:

`SOURCE_BLOCKED_FULL_EXPORT_LOGIN_REQUIRED`

Für die übrigen fehlenden Segmente verwendet v0.28 bewusst nur den konservativen Status:

`NOT_IMPORTED_OFFICIAL_FULL_SOURCE_NOT_MATERIALIZED`

Es werden keine unbewiesenen Detailursachen erfunden.

## 4. Identity-Reconciliation

Der Stage prüft für jede aktuelle Masterzeile:

- WS_ID
- ISIN
- Primary MIC
- Primary Ticker

Zulässige Identitätsklassen:

- `ISIN_MIC_TICKER_STRICT_IDENTITY`
- `MIC_TICKER_WSID_FALLBACK_IDENTITY` nur wenn die offizielle Quelle keine ISIN liefert
- `IDENTITY_INCOMPLETE_OR_INVALID`

Duplicate WS_ID werden fail-closed behandelt.

Zusätzlich wird der 1535er Research-Snapshot exakt gegen die Master-Identity-Keys reconciliert.

## 5. Source-Authority-Audit

Für die sieben vorhandenen Segmente wird nicht bloß aus ihrer Existenz im Master behauptet, dass die
vollständige Source-Provenance bereits eingefroren sei.

v0.28 kennzeichnet sie deshalb als:

`CURRENT_MASTER_LINEAGE_IMPORTED_BUT_SOURCE_EVIDENCE_AUDIT_REQUIRED`

Der nächste Schritt muss die explizite offizielle Source-Provenance je Segment materialisieren/frieren.

## 6. Freeze-Gates

v0.28 darf **nicht** erzeugen:

- finalen `SOURCE_SUPERSET_FROZEN`,
- `SWING_U3K_ELIGIBLE`,
- `SWING_U3K_FROZEN`,
- P0-Ergebnis,
- Sector RS,
- produktive Trading-Autorität.

Solange 7/14 Segmente fehlen gilt:

`BLOCKED_CURRENT_MASTER_SOURCE_SUPERSET_INCOMPLETE_7_OF_14`

## 7. Historische 1535-Price-Coverage

`output_research_1535/coverage.json` wird nur als eingefrorener historischer Kontext übernommen.

Sie ist vom 23.08.2026 und darf nicht als Beweis aktueller Preisfrische verwendet werden.

Daher führt v0.28 keine Preisentscheidung auf Basis dieses Files aus.

## 8. Outputs

- `current_master_segment_inventory_v0.28.csv`
- `current_master_identity_quality_v0.28.csv`
- `current_master_source_authority_audit_v0.28.csv`
- `current_master_blocker_register_v0.28.csv`
- `current_master_workbook_sheet_inventory_v0.28.csv`
- `lineage_authority_matrix_v0.28.csv`
- `freeze_plan_v0.28.csv`
- `summary_v0.28.json`
- `stage_checkpoint_v0.28.json`
- `manifest_v0.28.json`

Zusätzlich:

- `WELT-SWING-CURRENT-Handoff-v0.28.md`
- `WELT-SWING-CURRENT-Handoff-CURRENT.md`

## 9. Verbindliche Current-Handoff-Regel ab v0.28

Jeder größere weitere DEV-Stage soll den Current Handoff aktualisieren.

Es werden zwei Fassungen gepflegt:

1. **versioniert** für Audit/Historie,
2. **stabiler CURRENT-Alias** für schnelle Wiederherstellung.

Der stabile Recovery-Pfad lautet künftig:

`DEV Master → WELT-SWING-CURRENT-Handoff-CURRENT.md → aktueller Checkpoint/Manifest → aktuelle Universe-Artefakte`

Dadurch soll eine Rekonstruktion nicht mehr von Chat-Kontext oder Erinnerung abhängen.

## 10. Nächster Stage

`CURRENT_MASTER_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION`

Ziel:

- offizielle Source-Provenance der sieben vorhandenen Segmente einfrieren,
- fehlende sieben Segmente ausschließlich über zulässige offizielle Vollquellen materialisieren,
- Blocker explizit beibehalten, wenn eine offizielle Vollquelle nicht verfügbar ist,
- keine Drittquellen-Substitution.
