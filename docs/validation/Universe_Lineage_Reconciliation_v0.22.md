# WELT-SWING LONG DEV — Universe Lineage Reconciliation v0.22

**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Stage:** `UNIVERSE_LINEAGE_RECONCILIATION_AND_COVERAGE_GATE`

## Zweck

v0.22 stoppt vorerst die weitere P0-/Sector-RS-Ausweitung und klärt deterministisch die
Universe-Lineage zwischen dem vollständigen Source-Superset und dem eingefrorenen
2.037-Zeilen-Research-Partial/P0-Pfad.

Der Anlass ist die regionale Schieflage des Research-Partial:
Europa ist dort nicht enthalten, während die USA stark vertreten sind.

## Bereits durch die eingefrorenen Vorgängerartefakte belegter Ausgangspunkt

Das Phase-2-Source-Superset enthält alle 14 Zielsegmente und 3.664 Source-Zeilen.
Darunter:

- `EU_STOXX600`: 600
- `US_SP1500`: 1.506

Der aktive Full-Price-Source-Snapshot enthält 3.663 Zeilen.

v0.16 friert dagegen nur 2.037 verifizierte Strict-Zeilen ein.
Die eingefrorene Segment-Coverage weist aus:

- Europa: 600 Full-Eligibility, 0 Strict, 365 Instrument-unresolved, 235 andere Non-Strict.
- USA: 1.505 Full-Eligibility, 1.332 Strict, 0 Instrument-unresolved, 173 andere Non-Strict.
- Insgesamt: 3.657 Full-Eligibility, 2.037 Strict, 650 Instrument-unresolved, 970 andere Non-Strict.

v0.21 verwendet weiterhin diese 2.037-Zeilen-Lineage. 2.036 Zeilen sind dort
AsOf-synchronisiert; `WS:US:WBS` bleibt fail-closed.

## Was v0.22 tut

v0.22 liest ausschließlich eingefrorene Repository-Artefakte und rekonstruiert die
Mengenbeziehungen pro `WS_ID` und pro `Primary_Universe_Index`.

Jede der 3.663 aktiven Source-Zeilen wird genau einer Lineage-Klasse zugeordnet:

1. `INCLUDED_RESEARCH_PARTIAL_VERIFIED_STRICT`
2. `EXCLUDED_INSTRUMENT_TYPE_NOT_YET_STRICTLY_VERIFIED`
3. `EXCLUDED_OTHER_NON_STRICT_REASON_NOT_CLASSIFIED_V0_22`
4. `ABSENT_FROM_V0_14_FULL_ELIGIBILITY_REASON_NOT_CLASSIFIED_V0_22`

Die letzten beiden Klassen sind absichtlich keine Ursachenbehauptung. v0.22 bestätigt dort
nur die Mengendifferenz. Eine fachliche Ursache darf erst in einem separaten
Root-Cause-Audit vergeben werden.

## Erwartete Kernaussage

Wenn alle Gates bestehen, ist die Universe-Frage präzise beantwortet:

- Europa fehlt **nicht** im kanonischen Source-Universe.
- Europa fehlt im eingefrorenen Research/P0-Pfad, weil in v0.16 keine der 600 aktiven
  STOXX-600-Zeilen zum verifizierten Strict-Subset gehörte.
- 365 europäische Zeilen sind nachweislich Instrument-unresolved.
- Die verbleibenden 235 europäischen Zeilen sind nachweislich andere Non-Strict-Zeilen;
  v0.22 weist ihnen noch keinen ungeprüften Grund zu.
- Die USA sind im Source-Universe mit 1.506 aktiven Zeilen enthalten; 1.332 davon liegen
  im v0.16-Strict-Subset.
- Ein US-Source-Datensatz liegt außerhalb der v0.14-Full-Eligibility; der Grund wird in
  v0.22 nicht geraten.
- Der Research/P0-Pfad bleibt damit ein `RESEARCH_PARTIAL`, kein global vollständiges
  Strict-Universe.

## Coverage Gate

`global_p0_coverage_gate = BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT`

Das bedeutet nicht, dass v0.22 fehlgeschlagen ist. Der v0.22-Audit kann `SUCCESS` sein,
während das globale P0-Coverage-Gate weiterhin blockiert bleibt.

## Nicht erlaubt in v0.22

Keine Netzwerkaufrufe, keine neuen Kursdaten, keine FX-/News-/Fundamentaldaten, kein
Sector RS, keine P0-Schwellen, keine Lane-PASS/FAIL-Entscheidungen, keine Survivors,
keine Änderung des kanonischen Universe und keine produktive Trading-Autorität.
Alpha Vantage bleibt verboten.

## Outputs

- `universe_lineage_row_reconciliation_v0.22.csv`
- `universe_lineage_segment_reconciliation_v0.22.csv`
- `universe_gap_classification_v0.22.csv`
- `lineage_source_registry_v0.22.json`
- `summary_v0.22.json`
- `stage_checkpoint_v0.22.json`
- `manifest_v0.22.json`

## Nächster Schritt nach erfolgreicher Abnahme

`UNIVERSE_GAP_ROOT_CAUSE_AUDIT_AND_REMEDIATION_PLAN`

Dieser nächste Schritt muss insbesondere die 970 `OTHER_NON_STRICT`-Zeilen und die
6 aktiven Source-Zeilen außerhalb der v0.14-Full-Eligibility ursächlich auflösen.
Erst danach wird entschieden, welche Coverage-Remediation vor Sector-RS/P0-Promotion
technisch und methodisch zulässig ist.

## Result wording

Erlaubt:
`bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage`

Nicht erlaubt:
`weltweit bester Kandidat`
