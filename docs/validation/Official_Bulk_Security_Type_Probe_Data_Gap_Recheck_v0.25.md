# WELT-SWING LONG DEV — Official Bulk Security-Type Probe & Data-Gap Recheck v0.25

**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Stage:** `OFFICIAL_BULK_SECURITY_TYPE_PROBE_AND_DATA_GAP_RECHECK`

## Zweck

v0.25 ist der erste Netzwerk-Stage nach v0.24. Er führt ausschließlich begrenzte Abfragen offizieller
Börsen-/Marktplatzquellen aus. Ziel ist Source Capability und Materialisierbarkeit, nicht die unmittelbare
Klassifikation der 650 offenen Instrumente.

Parallel werden die 60 echten Datenlücken gegen den neuesten eingefrorenen Repository-Stand erneut geprüft.
Es erfolgen dabei keine neuen Kurs- oder FX-Downloads.

## Ausgangslage

v0.24 ist erfolgreich abgeschlossen. Offene Instrument-Evidence:

- EU_STOXX600: 365
- CA_TSX: 105
- KR_KOSPI200: 92
- HK_HSI: 82
- MX_IPC: 6

Europa umfasst 16 MICs / 18 Country-MIC-Routen. Die größten Blöcke sind XLON 82, XETR 53,
XPAR 45, XSWX 34, XMIL 32 und XSTO 25.

## Bounded Official Source Probes

v0.25 konfiguriert genau 11 GET-Abfragen. Keine Abfrage wird pro Aktie wiederholt.

Europa:
- London Stock Exchange — Issuers and Instruments Reports (`XLON`)
- Deutsche Börse Xetra — List of Tradable Shares (`XETR`)
- Euronext — Stocks all markets (`XPAR`, `XAMS`, `XBRU`, `XLIS`, `XMIL`, `XOSL`, `XDUB`)
- SIX Swiss Exchange — Equities (`XSWX`)
- Nasdaq Nordic — European Equities (`XSTO`, `XCSE`, `XHEL`)
- Warsaw Stock Exchange — listed companies (`XWAR`)
- Vienna Stock Exchange — companies list (`XWBO`)

Für `XMAD` wird bewusst keine ungeprüfte Bulk-URL erfunden. Die 17 Titel bleiben als nicht konfigurierte
Source-Route sichtbar, bis ein belastbarer offizieller Bulk-/Security-Type-Zugang materialisiert ist.

Globale Segmente:
- HKEX Full List of Securities — offizielles XLSX, wird erneut materialisiert und auf Category/Sub-Category/ISIN geprüft.
- TMX TSX Listed Company Directory — Capability Probe; mögliche Downloadlinks werden nur entdeckt.
- KRX Data Marketplace — Capability-/Transportprobe.
- BMV Empresas Listadas — Capability Probe.

## Keine automatische Klassifikation

HTTP-OK oder eine Seite mit `Shares` reicht nicht für einen strikten Ordinary/Common-Share-PASS.
Auch ein maschinenlesbarer Bulkdatensatz wird in v0.25 nur als Evidence materialisiert.

Neue Instrumententscheidungen: **0**.

Verboten bleiben:
- Indexmitgliedschaft als Ersatz für Security-Type-Evidence,
- Company-Name-Guessing,
- per-security Web-Fanout,
- stilles Mischen verschiedener Security-Type-Semantiken,
- Gleichsetzung von `Equity` und `Ordinary Share` ohne dokumentierte offizielle Semantik.

## Kandidatenlinks

Offizielle HTML-Seiten werden nach potenziellen Bulk-/Downloadlinks durchsucht. Gefundene Links werden
in `official_candidate_links_v0.25.csv` gespeichert, aber in v0.25 nicht automatisch aufgerufen.

## Data-Gap-Recheck

Die 60 v0.24-Datenfälle werden vollständig rechecked, ausschließlich aus eingefrorener Repository-Evidence:
- 55 `DATA_HISTORY_REMEDIATION_CANDIDATE`
- 5 `DATA_OR_FX_VERIFICATION_CANDIDATE`

Es gibt keine automatische Eligibility-Promotion.

## Statuslogik

`SUCCESS`: alle 11 konfigurierten offiziellen Source-Probes liefern HTTP-OK.  
`PARTIAL`: mindestens eine Source-Route ist technisch blockiert, der Audit wurde aber vollständig und
fail-closed abgeschlossen.

Ein Source-HTTP-Fehler ist kein Produktfehler und kein Grund, eine Instrumentregel zu lockern.

## Outputs

- `official_source_probe_status_v0.25.csv`
- `official_candidate_links_v0.25.csv`
- `eu_official_probe_route_coverage_v0.25.csv`
- `global_instrument_probe_state_v0.25.csv`
- `data_gap_recheck_v0.25.csv`
- `data_gap_recheck_counts_v0.25.csv`
- `source_materialization_followup_v0.25.csv`
- `raw_official_probe/*`
- `summary_v0.25.json`
- `stage_checkpoint_v0.25.json`
- `manifest_v0.25.json`

## Governance

- maximal 11 konfigurierte externe Requests
- keine per-security Requests
- Alpha Vantage verboten
- keine Kursdownloads
- keine FX-Downloads
- kein Sector RS
- keine P0-Entscheidungen
- keine produktive Trading-Autorität
- keine Master-Mutation
- keine Mutation historischer Artefakte
- keine Regelabsenkung zur Coverage-Verbesserung

Coverage-Gate:
`BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT`

## Nächster Stage

`OFFICIAL_SOURCE_MATERIALIZATION_AND_DATA_GAP_REPAIR`

Nur tatsächlich gefundene, offizielle und nach Herkunft geprüfte Bulk-Kandidaten dürfen weiter materialisiert
werden. Neue Instrument-PASS/FAIL-Entscheidungen gehören erst in einen separaten nachfolgenden Klassifikationsstage.
