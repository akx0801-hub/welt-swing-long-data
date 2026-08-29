# WELT-SWING LONG DEV — Official Source Materialization & Data-Gap Repair v0.26

**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Stage:** `OFFICIAL_SOURCE_MATERIALIZATION_AND_DATA_GAP_REPAIR`

## Scope und Lineage

v0.26 arbeitet ausdrücklich auf der **Legacy-/Pre-Master-Research-Lineage** aus Phase2 → v0.14–v0.25.
Die Arbeit an diesen 650 Instrument-Evidence-Fällen und 60 Datenfällen stellt **keine** aktuelle
Master-konforme globale U3K-Source-Coverage her.

Daher bleiben:

- `current_master_canonical_universe_reconciled = false`
- `strict_u3k_frozen = false`
- `productive_trading_authority = false`

## Ausgangspunkt v0.25-r3

Der abgenommene v0.25-r3-Stage ist korrekt `PARTIAL`:

- 650 Instrument-Evidence-Fälle: EU 365 / CA 105 / KR 92 / HK 82 / MX 6
- 11 offizielle Source-Probes, davon 10 HTTP-OK
- KRX als echter Source-Blocker
- 1 geparste offizielle Bulk-Referenz: HKEX
- 244 eingefrorene offizielle Kandidatenlinks
- 60 Datenfälle: 55 History + 5 Data/FX
- 0 Instrumententscheidungen
- 0 Eligibility-Promotions

## HKEX: Materialisierung ohne Instrumententscheidung

v0.26 liest die bereits eingefrorene offizielle HKEX-XLSX und erkennt die echte Headerzeile über
`Stock Code`, `Category`, `Sub-Category` und `ISIN`.

Die 82 offenen HSI-Zeilen müssen exakt denselben `WS_ID`-Satz wie die v0.9-HKEX-Matches bilden.
Jeder eingefrorene Stock Code wird erneut gegen die aktuelle offizielle Bulkdatei gematcht; vorhandene
ISIN-Evidence muss kompatibel bleiben.

Outputs:

- `hkex_current_exact_match_audit_v0.26.csv`
- `hkex_current_category_counts_v0.26.csv`

Auch ein erfolgreicher Match wird in v0.26 **nicht** in `Instrument PASS` umgewandelt. Die offizielle
Semantik für Common-/Ordinary-Shares wird erst im nächsten Requalification-Stage bewertet.

## 244 Kandidatenlinks: Offline-Priorisierung

Die in v0.25 gefundenen Links werden ausschließlich offline priorisiert. Höhere Scores erhalten
maschinenlesbare Endungen sowie Begriffe wie `download`, `instrument`, `security`, `equity`, `share` und
`list`.

v0.26 ruft **keinen** dieser 244 Links auf.

Outputs:

- `official_candidate_link_priority_v0.26.csv`
- `official_candidate_link_shortlist_v0.26.csv`

## KRX und Spanien bleiben fail-closed

KRX bleibt:

`BLOCKED_HTTP200_ERROR_503_CARRIED_FORWARD`

Die 17 `XMAD`-Fälle bleiben:

`UNCONFIGURED_OFFICIAL_BULK_ROUTE_CARRIED_FORWARD`

Es wird keine BME-URL geraten und keine Drittquelle als Ersatz akzeptiert.

## Reparatur der 55 History-Datenlücken

Die Zielmenge ist hart eingefroren:

- exakt 55 `DATA_HISTORY_REMEDIATION_CANDIDATE`
- exakt derselbe `WS_ID`-Satz wie `QA v0.4 residual_non_ready`
- remediated master: 3.657 aktive Zeilen
- restored QA-v0.4 cache: 3.657 states
- baseline READY: 3.602
- baseline non-READY: exakt diese 55 Zielzeilen

Nur diese 55 Historien werden in einer **Arbeitskopie** des SQLite-Caches gelöscht und anschließend über
den bestehenden yfinance-Free-Data-Core als 2-Jahres-Batch neu geladen.

Konfiguration:

- `batch_size = 20`
- `initial_period = 2y`
- `repair_anomalies = true`
- Alpha Vantage verboten
- keine title-spezifischen Web-/News-Abfragen

`DOWNLOAD_FAILED` oder `MAPPING_PENDING` blockieren die Cache-Promotion. Andere Zustände bleiben legitime
Diagnosen und werden nicht durch schwächere Regeln in Eligibility-PASS umgewandelt.

## Fünf Data/FX-Fälle

Die fünf `DATA_OR_FX_VERIFICATION_CANDIDATE` werden getrennt eingefroren als:

`data_or_fx_recompute_queue_v0.26.csv`

Die eigentliche Liquiditäts-/FX-Neuberechnung gehört in den nächsten Requalification-Stage.

## Cache-Promotion ist keine Eligibility-Promotion

Wenn die 55 Target-Downloads keine Hard Failures enthalten, darf die Arbeitskopie als neuer Main-Price-Cache
gespeichert werden. Das bedeutet ausschließlich **Price-cache data promoted** und ausdrücklich nicht
Instrument PASS, Eligibility PASS, P0 PASS oder produktive Trading-Freigabe.

## Governance

Unverändert verboten:

- Alpha Vantage
- 244 Candidate-Link-Requests
- per-security News-/Fundamental-Web-Fanout
- neue Instrument-PASS/FAIL-Entscheidungen
- Eligibility-Promotions
- Sector RS
- P0
- produktive Trading-Autorität
- Mutation historischer Artefakte
- Regelabsenkung zur Coverage-Verbesserung

Das globale Coverage-Gate bleibt:

`BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT`

## Nächster Stage

`OFFICIAL_SECURITY_TYPE_SEMANTICS_AND_REPAIRED_DATA_REQUALIFICATION`

Dort dürfen die materialisierte HKEX-Semantik und die reparierten Price-Cache-Zustände getrennt
requalifiziert werden. Die Legacy-/Pre-Master-Lineage bleibt weiterhin strikt von der
current-master-kompatiblen Clean-Restart-Lineage getrennt.
