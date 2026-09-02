# Current Master Research Partial 1633 – v0.40 FIX2 DQ Dependency Retry

## Zweck

Dieser technische Korrekturlauf schließt ausschließlich den offenen Runtime-Fehler des erfolgreichen v0.40-Runs `33649915242`.

Im v0.40-Log wurden für drei QA-Reparaturen keine fachlich verwertbaren Provider-Ergebnisse erzeugt, weil die Runtime-Abhängigkeit `scikit-learn` fehlte:

- `WS:XLON:ROR.L` / `ROR.L`
- `WS:XTSE:IAU` / `IAU.TO`
- `WS:XTSE:LAC` / `LAC.TO`

Der Modus lautet ausschließlich:

`DQ_DEPENDENCY_RETRY_ONLY`

Dies ist weiterhin `DEV / RESEARCH / SHADOW` und nicht produktiv.

## Gefrorene Quelle

Ausgangsbasis ist der v0.40-Ergebniscommit:

`dc19cb39d456cd2c3b25f1c6efe42fe52fc3d63c`

sowie exakt der aus Run `33649915242` gespeicherte Actions-Cache:

`current-master-1633-v0.40-controlled-remediation-33649915242`

Erwartete Cache-Eigenschaften:

- SHA256: `ffffd708a04a795d09e2ead30e36f6df2c4d5316a26ace7bcc46805a5b41ac71`
- `price_daily = 675043`
- `cache_state = 1614`
- `batch_log = 26`

Der Restore ist fail-closed. Ein Cache-Miss oder eine SHA-/Count-Abweichung beendet den Lauf.

## Dependency-Gate

Vor jeder Cache-Kopie oder -Mutation müssen folgende Module importierbar sein:

- `yfinance`
- `pandas`
- `numpy`
- `scipy`
- `sklearn`

Der Workflow installiert ausdrücklich `scikit-learn`.

Zusätzlich wird das vollständige FIX2-Ausführungslog gespeichert. Die Marker

- `ModuleNotFoundError`
- `No module named`
- `ImportError`
- `Traceback (most recent call last)`

sind harte Fehler und verhindern Strong Gates, Commit und Cache-Save.

Damit kann ein Runtime-/Dependency-Fehler nicht erneut als scheinbares `NO_DATA_IN_BATCH` durchrutschen.

## Exakter Scope

Netzwerkzugriffe sind ausschließlich für die drei oben genannten QA-WS_IDs und ihre bereits eingefrorenen Provider-Symbole zulässig.

Alle drei Requests verwenden:

- `repair_pass = true`
- Start inklusiv `2024-09-01`
- Ende exklusiv `2026-09-01`
- Safe Cutoff `2026-08-31`

Es gibt genau einen logischen Provider-Batch. Pro Batch bleibt maximal ein identischer technischer Retry zulässig.

Nicht zulässig sind:

- die 151 Mapping-Retries erneut auszuführen;
- die übrigen vier QA-Fälle erneut auszuführen;
- die 88 Manual-Review-Mappingfälle anzufassen;
- Provider Search;
- FX;
- Alpha Vantage;
- Mapping Overrides;
- Universe-Mutation;
- Eligibility-Promotion;
- P0;
- Sector RS;
- SWING_U3K_FROZEN-Mutation.

## Cache-Isolation

Der wiederhergestellte v0.40-Cache ist reine Quelle. FIX2 erstellt eine separate Kopie:

`runtime_cache/v0_40_fix2/current_master_1633_controlled_remediation_fix2.sqlite`

Nur die drei Target-WS_IDs dürfen in dieser Kopie verändert werden.

`price_daily` und `cache_state` aller Nicht-Targets werden vor und nach FIX2 deterministisch gehasht. Jede Veränderung außerhalb der drei Targets ist ein harter Fehler.

## Konsolidierter Abschluss

FIX2 schreibt die drei neuen Resultate nicht in die historischen v0.40-Ausgaben zurück.

Stattdessen entstehen neue, nachvollziehbare Closeout-Dateien:

- `final_data_quality_results_7_v0.40.csv`
- `final_controlled_results_158_v0.40.csv`
- `final_residual_non_ready_158_v0.40.csv`

Die 151 Mapping-Ergebnisse aus v0.40 bleiben dabei byte-identische Eingangs-Evidenz. Die vier bereits technisch gültigen QA-Ergebnisse aus v0.40 werden übernommen; nur ROR.L, IAU.TO und LAC.TO werden durch FIX2-Ergebnisse ersetzt.

## Strong Gates

Der Lauf darf nur erfolgreich schließen, wenn insbesondere gilt:

- Source-Commit ist Ancestor;
- eingefrorene v0.40-Input-Blobs stimmen exakt;
- exakter Actions-Cache wurde wiederhergestellt;
- Source-Cache SHA/Counts unverändert;
- Dependency-Preflight erfolgreich;
- keine Runtime-Error-Marker im Ausführungslog;
- exakt drei Target-WS_IDs;
- exakt drei freigegebene Provider-Symbole;
- ausschließlich `repair=true`;
- exakt ein Provider-Batch;
- keine Bars nach `2026-08-31` für die drei Targets;
- Non-Target-Digest unverändert;
- finale DQ-Datei exakt 7 eindeutige Werte;
- finale kontrollierte Ergebnisdatei exakt 158 eindeutige Werte;
- keine Mapping-/Universe-/Eligibility-/Produktivmutation.

## Workflow

Der Workflow besitzt ausschließlich `workflow_dispatch`.

Das Hochladen von Script, Config, Workflow und Dokumentation startet daher nichts automatisch.

Nach bestandenen Strong Gates werden ausschließlich die neuen FIX2-Outputs committed und der isolierte FIX2-Arbeitscache unter einem neuen Cache-Key gespeichert.

## Nächster Schritt

Nach erfolgreichem FIX2-Closeout geht es weiter mit:

`CURRENT_MASTER_RESEARCH_PARTIAL_1633_MANUAL_MAPPING_EVIDENCE_REVIEW`

Ein erneutes blindes Same-Symbol-Retry der 151 Mappingfälle ist nicht vorgesehen.
