# Current Master Research Partial 1633 – Controlled Data Gap Remediation v0.40

## 1. Zweck und Modus

`CURRENT_MASTER_RESEARCH_PARTIAL_1633_CONTROLLED_DATA_GAP_REMEDIATION` ist der kontrollierte Netzwerk-Remediation-Stage nach dem abgeschlossenen v0.39 `DATA_GAP_AUDIT_ONLY`.

Der einzige zulässige Run-Modus ist `CONTROLLED_RETRY_DATA_ONLY`. Der Stage bleibt vollständig `DEV / RESEARCH / SHADOW` und nicht produktiv.

## 2. Gefrorene Ausgangsbasis

Ausgangsbasis ist der erfolgreiche v0.39 Ergebniscommit `66d9e2ec1eb8ba6ebc3c402854317c6216fccad5`.

v0.39 hat 249 offene Auditfälle klassifiziert: 158 `RETRY_DATA`, 88 `MANUAL_REVIEW` und 3 `DEFER_TEMPORAL`. Die 158 freigegebenen `RETRY_DATA`-Fälle bestehen exakt aus 151 `MAPPING / EXACT_PROVIDER_SYMBOL_NO_DATA`, 2 `INVALID_BAR_TARGETED_REPAIR_CANDIDATE` und 5 `SUSPICIOUS_RETURN_TARGETED_REPAIR_CANDIDATE`. Zusätzlich bleiben 19 strukturelle Instrument-FAILs geschützt und außerhalb jeder Datenrettung.

## 3. Exakter Target Scope

Der v0.40-Lauf darf ausschließlich die 158 v0.39-`RETRY_DATA`-WS_IDs an den Provider übergeben. Ausgeschlossen und durch Strong Gates geschützt sind alle 88 `MANUAL_REVIEW`-Mappingfälle, alle 3 `HISTORY / DEFER_TEMPORAL`-Fälle, alle 19 strukturellen Instrument-FAILs und alle übrigen bereits technisch bereiten Werte.

Für die 151 Mapping-Retries gilt zwingend: `Static_Symbol_Relation = EXACT`, `Prior_Yahoo_Symbol == Candidate_Yahoo_Symbol`, kein Candidate Override, keine Namenssuche, keine Provider-Symbolsuche und keine ADR-/Sekundärlisting-Substitution.

## 4. Netzwerkvertrag

Zulässig ist ausschließlich `YFINANCE_FREE` für OHLCV-Downloads der 158 freigegebenen Targets. Für die 151 Mappingfälle gibt es einen normalen Fixed-Window-Bulk-Pass und höchstens einen gruppierten Fixed-Window-Rescue-Pass für Symbole, die im ersten Bulk-Response fehlen. Für die 7 bereits freigegebenen QA-Fälle gibt es einen gezielten `repair=True` Fixed-Window-Pass. Pro Batch ist höchstens ein identischer technischer Retry erlaubt, entsprechend dem bereits auditierten `price_cache.py`.

Verboten sind Provider Search, FX-Download, Alpha Vantage, neue Mapping-Kandidaten, andere Listings/Provider und nicht freigegebene WS_IDs.

Der Request-Zeitraum ist fest: Start inklusiv `2024-09-01`, Ende exklusiv `2026-09-01`, sicherer letzter Bar-Tag `2026-08-31`. Damit können keine September-Bars in den Research-Snapshot gelangen.

## 5. Cache-Isolation

Der eingefrorene v0.38-Cache `runtime_cache/v0_38/current_master_1633_market_prices.sqlite` bleibt unverändert. Er muss vor und nach dem Lauf exakt SHA-256 `d466ae08fc22c5bcae86dacb88759773565552cd58e17640d971d191c83311d0` sowie `price_daily=676550`, `cache_state=1614`, `batch_log=21` besitzen.

v0.40 erstellt eine isolierte Kopie `runtime_cache/v0_40/current_master_1633_controlled_remediation.sqlite`. Nur dort werden die 158 Target-WS_IDs vor dem Full-Window-Refresh gelöscht und neu materialisiert. Die Nicht-Target-Zeilen von `price_daily` und `cache_state` werden vor und nach dem Lauf deterministisch gehasht. Jede Veränderung außerhalb der 158 Targets lässt den Lauf scheitern. Neue `batch_log`-Zeilen sind als Provider-Auditspur zulässig.

## 6. Mapping-Retry 151

Die 151 Mappingfälle werden ausschließlich mit dem bereits eingefrorenen exakt gleichen Provider-Symbol abgefragt. Der erste Pass heißt `MAPPING_NORMAL`. Fehlt ein Symbol innerhalb des Bulk-Responses, darf es genau einmal in einen gruppierten `MAPPING_RESCUE` übernommen werden. Auch der Rescue verwendet dasselbe Symbol und dasselbe feste Datumsfenster.

Ein erfolgreich zurückgeliefertes Preis-Set ist lediglich neue Mapping-/Daten-Evidenz. Es erzeugt weder einen Universe-Override noch eine Eligibility-Promotion.

## 7. QA-Repair 7

Die sieben in v0.39 freigegebenen QA-Fälle werden mit ihrem bestehenden Yahoo-Symbol und `repair=True` über dasselbe feste Vollhistorienfenster neu geladen. Die alte Target-Serie wird nur in der isolierten v0.40-Arbeitskopie vorher entfernt, damit malformed oder suspicious Bars nicht als verwaiste Cache-Zeilen erhalten bleiben.

Mögliche Post-States sind `READY`, `WARMUP`, `QUARANTINE`, `DOWNLOAD_FAILED` oder `STALE`. `READY` bedeutet in diesem Stage nur `RECOVERED_READY_EVIDENCE_ONLY` und ausdrücklich noch keine Eligibility-Promotion.

## 8. Outputs

Der Stage schreibt ausschließlich nach `output_current_master_research_partial_1633_controlled_data_gap_remediation_v0_40/`.

Kernoutputs sind `target_plan_158_v0.40.csv`, Before-/After-State und Price-Counts, `logical_batch_plan_v0.40.csv`, `provider_request_ledger_v0.40.csv`, `mapping_missing_after_normal_v0.40.csv`, `provider_batch_log_new_v0.40.csv`, `controlled_results_158_v0.40.csv`, `mapping_retry_results_151_v0.40.csv`, `data_quality_repair_results_7_v0.40.csv`, `residual_non_ready_v0.40.csv`, `summary_v0.40.json`, `stage_checkpoint_v0.40.json` und `manifest_v0.40.json`.

## 9. Strong Gates

Die Strong Gates erzwingen mindestens: exakte v0.39-Input-Blobs, unveränderten Source-Cache, exakt 158 eindeutige Targets, exakt 151 Mapping-Retries und 7 QA-Repairs, keine Requests aus den 88 Manual-Review-, 3 History- oder 19 Instrument-Fail-Fällen, Mapping nur mit `repair=False`, DQ nur mit `repair=True`, festes Datumsfenster, höchstens einen identischen Retry pro Batch, keine Bars nach 2026-08-31, unveränderten Nicht-Target-Cache-Digest, kein Provider Search, kein FX, kein Alpha Vantage, keinen Mapping-Override, keine Universe-Mutation, keine Eligibility-Promotion, kein P0, kein Sector RS, keine SWING_U3K_FROZEN-Mutation und nicht produktiven Status.

## 10. Workflow

Der Workflow besitzt ausschließlich `workflow_dispatch`; `push`, `schedule`, `pull_request` und `repository_dispatch` sind nicht erlaubt. Das Hochladen der vier v0.40-Dateien startet daher nichts automatisch. Erst nach separatem Pre-Run-Review wird genau ein manueller Lauf auf `main` freigegeben.

Nach bestandenen Strong Gates werden nur die v0.40-Outputs committed. Die isolierte v0.40-Arbeitscache wird unter einem neuen GitHub-Actions-Cache-Key gespeichert.

## 11. Nächster Stage

v0.40 löst die 88 `MANUAL_REVIEW`-Mappingfälle absichtlich nicht. Der nächste logische Schritt nach Review der v0.40-Ergebnisse ist `CURRENT_MASTER_RESEARCH_PARTIAL_1633_MANUAL_MAPPING_EVIDENCE_REVIEW`. Erst danach darf über aktuelle Eligibility-Recomputation und U3K-Input-Plan entschieden werden.
