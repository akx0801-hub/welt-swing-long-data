# Current Master Research Partial 1633 – Data Gap Remediation v0.39

## 1. Zweck und Status

`CURRENT_MASTER_RESEARCH_PARTIAL_1633_DATA_GAP_REMEDIATION` ist der fachlich nächste DEV/RESEARCH/SHADOW-Stage nach dem abgeschlossenen v0.38-Datenrefresh.

Die erste Phase ist ausschließlich:

`DATA_GAP_AUDIT_ONLY`

Sie klassifiziert die verbliebenen technischen Datenlücken. Sie repariert noch nichts und führt keinerlei Netzwerkzugriff aus.

Kein produktiver Eligibility-Lauf, kein P0, kein Sector-RS, keine SWING_U3K_FROZEN-Mutation und keine Universe-Mutation sind Bestandteil dieser Phase.

## 2. Gefrorene Ausgangsbasis

Die Ausgangsbasis ist der erfolgreiche v0.38-Ergebniscommit:

`03230b1409d8da7ec513f76383e18fcf07aef465`

Der v0.38-Abschlusszustand ist:

- Current Master: 1.633
- `READY_FOR_ELIGIBILITY_RECOMPUTE`: 1.365
- `MAPPING_DOWNLOAD_NO_DATA`: 239
- `HISTORY_DATA_QUALITY_FAIL`: 7
- `INSUFFICIENT_HISTORY_FOR_STANDARD_U3K`: 3
- strukturelle Instrument-FAILs: 19
- FX unresolved: 0

Daraus ergibt sich für den Audit eine disjunkte Zielmenge von 249 Fällen: 239 Mapping + 7 Data Quality + 3 History. Die 19 Instrument-FAILs werden separat als geschützte Exklusion dokumentiert und ausdrücklich nicht in die Datenrettung aufgenommen.

## 3. Audit-only-Prinzip

Der Audit darf ausschließlich vorhandene Evidenz lesen:

- v0.38 Mapping-Revalidation und Mapping-Remediation-Queue
- v0.38 History Gate
- v0.38 Data-Quality Exceptions
- v0.38 Current Data Readiness und Summary
- gefrorener v0.38 SQLite-Preis-Cache im Read-only-Modus

Der Cache muss exakt den bekannten SHA-256 und die bekannten Tabellenzählungen besitzen. Vor und nach dem Audit muss der SHA identisch sein.

Verboten sind:

- `yf.download()` oder andere Stock-/FX-Downloads
- Yahoo-/Provider-Suche
- Alpha Vantage
- automatische Provider-Symbolsuche
- automatische Mapping-Overrides
- ADR-/Sekundärlisting-Substitution
- Namenssuche zur Ticker-Ersetzung
- Universe-Mutation
- Eligibility-Promotion
- produktive Statusänderungen

Nach abgeschlossenem Pre-Run-Review wird ein eigener GitHub-Actions-Workflow angelegt. Er besitzt ausschließlich `workflow_dispatch` und keinen `push`, `schedule`, `pull_request` oder `repository_dispatch` Trigger. Dadurch kann weder das Hochladen der Config noch ein anderer normaler Commit den v0.39-Audit automatisch starten.

`network_allowed = false` bezieht sich auf den Audit-Code und Markt-/Provider-Datenzugriffe. GitHub-Actions-Infrastruktur wie Checkout, Python-Setup, Dependency-Installation und Cache-Restore ist davon nicht umfasst; der Audit selbst führt keine Provider-Suche und keine Stock-/FX-Netzwerkabfrage aus.

## 4. Mapping-Audit – 239 Fälle

Alle 239 Fälle stammen aus `MAPPING_DOWNLOAD_NO_DATA`.

Der Audit darf aus der vorhandenen statischen Evidenz nur Symbolbeziehungen diagnostizieren:

- `EXACT`: Prior- und Candidate-Yahoo-Symbol identisch
- `CASE_ONLY`: nur Groß-/Kleinschreibung geändert
- `SUFFIX_CHANGED`: gleicher Basis-Ticker, anderes Provider-Suffix
- `BASE_CHANGED` / `OTHER_TRANSFORM`: sonstige statische Transformation

Dispositionen:

- `EXACT_PROVIDER_SYMBOL_NO_DATA` -> `RETRY_DATA` / später ausschließlich kontrollierter Retry desselben Provider-Symbols
- `CASE_NORMALIZATION_SUSPECT` -> `MANUAL_REVIEW`
- `SUFFIX_MAPPING_SUSPECT` -> `MANUAL_REVIEW`
- sonstige Transformation -> `MANUAL_REVIEW`

Wichtig: `AUTO_FIX_SAFE` wird in dieser Audit-Phase absichtlich nie vergeben. Ein Symbol darf erst nach zusätzlicher externer Primärlisting-/Provider-Evidenz als Override freigegeben werden. Ebenso darf kein Mapping-Fall allein wegen `NO_DATA` als delistet oder terminal blockiert erklärt werden.

## 5. Data-Quality-Audit – 7 Fälle

Die sieben v0.38-Ausnahmen sind in der Quelle bereits eindeutig aufgeteilt:

- 2 × `INVALID_OHLC_OR_VOLUME`
- 5 × `SUSPICIOUS_RETURN_NEEDS_REPAIR`

Der Audit liest nur den gefrorenen Cache und rekonstruiert:

- ungültige OHLC-/Volume-Zeilen
- deren Anteil an den Cache-Zeilen
- >50-%-Return-Ereignisse
- Split-Evidenz im unmittelbaren Nachbarfenster
- vorhandene Bar-/Repair-Metadaten aus dem v0.38 History Gate

Mögliche Diagnoseklassen sind u. a.:

- `LIKELY_ISOLATED_INVALID_BARS_FILTERABLE`
- `INVALID_BAR_TARGETED_REPAIR_CANDIDATE`
- `LIKELY_SPLIT_OR_CORPORATE_ACTION`
- `SUSPICIOUS_RETURN_TARGETED_REPAIR_CANDIDATE`

Der Audit selbst verändert keine Daten. Ein späterer Repair ist immer auf einzelne explizit freigegebene Symbole begrenzt.

## 6. History-Audit – 3 Fälle

`WARMUP / INSUFFICIENT_HISTORY` wird nicht als Providerfehler behandelt.

Die bestehende Projektsemantik wird beibehalten:

`STRUCTURAL_TEMPORAL_EXCLUSION_UNTIL_HISTORY_MATURES`

Disposition:

`DEFER_TEMPORAL`

Aktion:

`KEEP_WARMUP_NO_REPAIR`

Zusätzlich werden nur `Bars_To_260` und `Bars_To_252_Valid` materialisiert. Es wird kein künstliches zukünftiges Reifedatum konstruiert.

## 7. Geschützte Instrument-FAILs – 19 Fälle

Die 19 strukturellen Instrument-FAILs bleiben explizit außerhalb des Audit-Targets und außerhalb jeder Datenrettung.

Audit-Aktion:

`PROTECTED_INSTRUMENT_FAIL_NO_DATA_REMEDIATION`

## 8. Outputs

Der Offline-Audit erzeugt ausschließlich unter:

`output_current_master_research_partial_1633_data_gap_remediation_v0_39/`

folgende Dateien:

- `mapping_gap_audit_239_v0.39.csv`
- `data_quality_gap_audit_7_v0.39.csv`
- `history_gap_audit_3_v0.39.csv`
- `protected_instrument_fail_19_v0.39.csv`
- `data_gap_audit_249_v0.39.csv`
- `remediation_queue_v0.39.csv`
- `invalid_bar_events_v0.39.csv`
- `suspicious_return_events_v0.39.csv`
- `summary_v0.39.json`
- `stage_checkpoint_v0.39.json`
- `manifest_v0.39.json`

Der Audit verändert weder v0.38-Handoffs noch v0.38-Outputs.

## 9. Strong Gates

Die Strong Gates prüfen mindestens:

- v0.39-Audit-Workflow vorhanden und ausschließlich manuell auslösbar (`workflow_dispatch`)
- Config autorisiert ausschließlich `MANUAL_DISPATCH_ONLY`

- exakten Source-Commit als Ancestor
- exakte eingefrorene v0.38-Git-Blobs
- exakten Cache-SHA und Tabellenzählungen
- Cache unverändert vor/nach Audit
- 239 Mapping-Fälle
- 7 Data-Quality-Fälle
- 3 History-Fälle
- 19 geschützte Instrument-FAILs
- 249 eindeutige, disjunkte Audit-Ziel-WS_IDs
- Mapping nur aus `MAPPING_DOWNLOAD_NO_DATA`
- kein Mapping `AUTO_FIX_SAFE`
- kein erzeugter Candidate Override
- keine unbelegte `TERMINAL_BLOCKED`-Einstufung
- Data Quality exakt 5 Suspicious Return + 2 Invalid OHLC/Volume
- History ausschließlich `STRUCTURAL_TEMPORAL_EXCLUSION_UNTIL_HISTORY_MATURES / DEFER_TEMPORAL / KEEP_WARMUP_NO_REPAIR`
- Netzwerkzugriffe = 0
- Stock-/FX-Downloads = false
- Provider Search = false
- Universe Mutation = false
- Eligibility Promotion = false
- P0 / Sector RS / SWING_U3K_FROZEN / Productive = false

## 10. Nächste Entscheidung nach Audit

Der Audit ist noch keine Remediation-Ausführung.

Erst nach Review der erzeugten Klassen und Queues wird ein separater kontrollierter Pfad vorbereitet:

`CURRENT_MASTER_RESEARCH_PARTIAL_1633_CONTROLLED_DATA_GAP_REMEDIATION`

Dieser spätere Pfad darf nur die explizit freigegebenen `RETRY_DATA`-Fälle anfassen. Mapping-Transformationen benötigen vorher externe Primärlisting-/Provider-Evidenz. History-Warmups werden nicht repariert. Die 19 strukturellen Instrument-FAILs bleiben ausgeschlossen.
