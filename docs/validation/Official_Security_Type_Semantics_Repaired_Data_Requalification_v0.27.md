# WELT-SWING LONG DEV — Security-Type Semantics & Repaired-Data Requalification v0.27

**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Stage:** `OFFICIAL_SECURITY_TYPE_SEMANTICS_AND_REPAIRED_DATA_REQUALIFICATION`

## 1. Zweck

v0.27 schließt den fachlich sinnvollen Requalifikationskreis von v0.26.

Der Stage bleibt ausdrücklich Teil der:

`LEGACY_PRE_MASTER_RESEARCH_LINEAGE`

Er stellt **keine** current-master-konforme globale U3K-Coverage her.

## 2. Wichtigster Befund aus v0.26

Die 55 gezielt neu geladenen Historien ergaben:

- 0 READY
- 49 QUARANTINE
- 6 WARMUP
- 0 Hard Failures

Damit ist ein weiterer pauschaler Redownload derselben 55 Zeilen nicht begründet.

v0.27 klassifiziert sie deterministisch:

| Cache-Status | Reason | v0.27-Behandlung |
|---|---|---|
| WARMUP | INSUFFICIENT_HISTORY | `STRUCTURAL_TEMPORAL_EXCLUSION_UNTIL_HISTORY_MATURES` |
| QUARANTINE | INVALID_OHLC_OR_VOLUME | `PERSISTENT_DATA_QUALITY_EXCLUSION` |
| QUARANTINE | SUSPICIOUS_RETURN_NEEDS_REPAIR | `PERSISTENT_SUSPICIOUS_RETURN_EXCLUSION` |

Jeder andere Zustand ist ein Fehler im Stage und wird nicht still akzeptiert.

## 3. Fünf Data/FX-Fälle

Die fünf in v0.26 separat eingefrorenen `DATA_OR_FX_VERIFICATION_CANDIDATE` werden jetzt in Shadow neu berechnet.

Verwendet werden ausschließlich:

- der promoted v0.26 SQLite-Price-Cache,
- die eingefrorene `fx_history_to_eur_v0.5.csv`,
- die unveränderte v0.5-Liquiditätsmethodik,
- die v0.5-Schwellen:
  - Preferred: mindestens 20 Mio. EUR Median-Turnover 20d,
  - Standard PASS: mindestens 15 Mio. EUR,
  - 5–15 Mio. EUR: `FAIL_STRICT`,
  - unter 5 Mio. EUR: `FAIL`.

**Current Cache Status ist das erste Gate.** Eine aktuell nicht-READY Zeile wird nicht aufgrund alter Queue-Werte nachträglich zu PASS gerechnet.

Die Ergebnisse heißen bewusst:

`Shadow_Liquidity_Gate_v0_27`

Sie verändern weder historische Strict Eligibility noch das aktuelle produktive Regelwerk.

## 4. HKEX

v0.26 hat für alle 82 offenen HSI-Fälle bestätigt:

- exakter Stock-Code-Match,
- ISIN-kompatibler Match,
- `Equity`,
- `Equity Securities (Main Board)`.

Das ist wertvolle offizielle Evidenz, aber noch kein hinreichender Beleg, dass jede einzelne Zeile im strikten
Master-Sinn eine zulässige `COMMON_STOCK` / `ORDINARY_SHARE` / `COMMON_SHARE` ist.

Deshalb lautet die v0.27-Semantik:

`HKEX_EQUITY_MAIN_BOARD_IDENTITY_VERIFIED_SUBTYPE_NOT_STRICTLY_PROVEN`

und die Instrumententscheidung bleibt:

`UNCHANGED_NOT_VERIFIED`

Es gibt **keine 82 künstlichen PASS-Promotions**.

## 5. Vollständiges 650er-Unresolved-Ledger

v0.27 schreibt die gesamte Legacy-Queue erneut als explizites Blocker-Ledger:

- 82 HKEX: Identity/Category materialisiert, Subtype nicht streng bewiesen,
- 92 KRX: offizieller Bulk-Source-Pfad weiterhin durch Error 503 blockiert,
- 17 XMAD: offizieller BME-Bulk-Pfad nicht konfiguriert,
- alle übrigen Fälle: offizielle Bulk-Security-Type-Evidenz weiterhin fehlend.

Damit bleibt die Coverage transparent und fail-closed.

## 6. Keine weitere Legacy-Endlosschleife

v0.27 führt bewusst nicht aus:

- weitere Preisdownloads,
- Abruf der 244 Candidate Links,
- neue Instrument-PASS/FAIL-Entscheidungen,
- Eligibility-Promotions,
- P0,
- Sector RS,
- News-/Fundamental-Fanout,
- Alpha Vantage,
- produktive Trading-Freigabe.

## 7. Erwartete Outputs

- `residual_data_quality_requalification_v0.27.csv`
- `residual_reason_counts_v0.27.csv`
- `data_or_fx_liquidity_recompute_v0.27.csv`
- `data_or_fx_liquidity_recompute_counts_v0.27.csv`
- `hkex_security_type_semantics_v0.27.csv`
- `unresolved_instrument_blockers_v0.27.csv`
- `legacy_requalification_impact_v0.27.csv`
- `summary_v0.27.json`
- `stage_checkpoint_v0.27.json`
- `manifest_v0.27.json`

## 8. Stage-Status

Auch bei technisch fehlerfreiem Lauf bleibt der fachliche Status voraussichtlich:

`PARTIAL`

Denn die Legacy-Instrument-Coverage ist nicht vollständig geklärt und insbesondere KRX bleibt source-blocked.

Das globale Gate bleibt:

`BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT`

## 9. Nächster Entwicklungsschritt

Nach v0.27 soll die Hauptentwicklung nicht weiter die alte Phase2-Lineage perfektionieren.

Der nächste Stage ist:

`CURRENT_MASTER_OFFICIAL_SOURCE_UNIVERSE_RECONCILIATION_AND_FREEZE_PLAN`

Dort wird die current-master-kompatible Clean-Restart-Lineage wieder zum primären Gegenstand:

1. offizielle Source-Coverage je Zielindex,
2. Identitäts-/Security-Type-/Liquidity-Gates,
3. explizite Blocker statt Drittquellenersatz,
4. deterministischer `SWING_U3K_ELIGIBLE`,
5. anschließend `SWING_U3K_FROZEN <= 3000`.

Erst danach ist ein neuer globaler Price/P0-Lauf fachlich sinnvoll.
