# WELT-SWING LONG DEV — Universe Gap Root Cause Audit v0.23

**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Stage:** `UNIVERSE_GAP_ROOT_CAUSE_AUDIT_AND_REMEDIATION_PLAN`

## Zweck

v0.23 löst die in v0.22 noch absichtlich nicht attribuierten Universe-Lücken auf,
ohne irgendeine Eligibility-Regel zu lockern.

Der Audit arbeitet ausschließlich mit bereits eingefrorenen Repository-Artefakten.
Es werden keine neuen Kurs-, FX-, News-, Fundamental- oder Webdaten geladen.

## Wichtige Korrektur aus der Lineage

v0.22 verglich den 3.663-Zeilen-Source-Snapshot mit der 3.657-Zeilen-v0.14-Eligibility.
Die Differenz von sechs Zeilen ist kein unbekannter technischer Datenverlust.

Die frühere `NON_READY_REMEDIATION_V0_2` dokumentiert:

- Source active vor Evidence-Remediation: 3.663
- Active nach Evidence-Remediation: 3.657
- delisted/retired exclusions: 6

Die sechs `EXCLUDE_INACTIVE`-Fälle sind:

- `WS:XASX:IFL` — Insignia Financial — `DELISTED_ACQUIRED`
- `WS:XASX:NSR` — National Storage REIT — `DELISTED_ACQUIRED`
- `WS:XMEX:ELEKTRA` — Grupo Elektra — `LISTING_REGISTRATION_CANCELLED`
- `WS:XNZE:ARV` — Arvida Group — `EQUITY_DELISTED_ACQUIRED`
- `WS:XNZE:MNW` — Manawa Energy — `EQUITY_DELISTED_ACQUIRED`
- `WS:US:CWEN.A` — Clearway Class A — `CLASS_A_CONVERTED_INTO_EXISTING_CLASS_C_ROW`

v0.23 verlangt, dass genau diese sechs IDs der v0.22-Klasse
`ABSENT_FROM_V0_14_FULL_ELIGIBILITY...` entsprechen.

Die separate Targeted-Refresh-6-Gruppe ist ausdrücklich **nicht** dieselbe Gruppe.
Das wird als eigener Gate geprüft.

## 970 OTHER_NON_STRICT — Root-Cause-Replay

Für die 970 `OTHER_NON_STRICT`-Zeilen wird keine neue Eligibility berechnet.
Stattdessen wird die bereits in v0.14 verwendete Priorität deterministisch als Audit
wiederholt:

1. `Cache_Status != READY`
2. `Liquidity_Gate != PASS`
3. `Scalable_Gate == FAIL`
4. `Instrument_Decision_v0_14 != PASS`

Zusätzlich wird für jede Zeile die vollständige Liste aller vorhandenen Blocker erhalten,
damit ein früher Blocker spätere Blocker nicht unsichtbar macht.

Remediation-Klassen:

- `DATA_HISTORY_REMEDIATION_CANDIDATE`
- `DATA_OR_FX_VERIFICATION_CANDIDATE`
- `VALID_STRICT_LIQUIDITY_EXCLUSION`
- `VALID_EXECUTION_GATE_EXCLUSION`
- `VALID_INSTRUMENT_GATE_EXCLUSION`
- `INSTRUMENT_EVIDENCE_REMEDIATION_CANDIDATE`

Ein Liquiditäts-Fail oder ein expliziter Instrument-Fail wird **nicht** repariert, indem
die Regeln gelockert werden.

## 650 Instrument-unresolved

Die 650 Zeilen aus der v0.15-Review-Queue müssen in v0.14 gleichzeitig erfüllen:

- Cache `READY`
- Liquidity `PASS`
- kein Scalable `FAIL`
- Instrument Decision `NOT_VERIFIED`
- Strict Eligibility `NOT_VERIFIED`

Sie werden als `INSTRUMENT_BULK_EVIDENCE_REQUIRED` klassifiziert und nach Segment,
Resolution Method und Resolution Reason ausgewiesen.

Bekannte Segmentzahlen bleiben als harte Gates erhalten:

- EU_STOXX600: 365 unresolved
- CA_TSX: 105
- KR_KOSPI200: 92
- HK_HSI: 82
- MX_IPC: 6

Europa bleibt damit der größte einzelne Instrument-Evidence-Block.

## Coverage-Denominator

Für den historischen v0.5–v0.15-Eligibility-Pfad beträgt der evidence-remediated
Denominator 3.657, nicht 3.663.

Damit beträgt die Strict-Coverage dieses historischen Eligibility-Scope:

`2.037 / 3.657 = 55,7014 %`

Das macht aus dem Research-Partial noch kein global vollständiges Strict-Universe.
Das globale P0-Coverage-Gate bleibt:

`BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT`

## Erwartete Outputs

- `historical_active_denominator_reconciliation_v0.23.csv`
- `other_non_strict_root_causes_v0.23.csv`
- `other_non_strict_root_cause_counts_v0.23.csv`
- `instrument_unresolved_root_causes_v0.23.csv`
- `instrument_unresolved_reason_counts_v0.23.csv`
- `segment_root_cause_matrix_v0.23.csv`
- `remediation_plan_v0.23.csv`
- `summary_v0.23.json`
- `stage_checkpoint_v0.23.json`
- `manifest_v0.23.json`

## Governance

Nicht erlaubt:

- per-security Web-Fanout
- neue Preis-/FX-/News-/Fundamentaldownloads
- Alpha Vantage
- Sector RS
- P0 PASS/FAIL
- Survivors
- produktive Trading-Autorität
- Änderung des kanonischen Masters
- Mutation historischer v0.5–v0.22-Artefakte
- Regelabsenkung zur Verbesserung regionaler Coverage

## Nächster Schritt

Nach erfolgreicher Abnahme:

`EU_INSTRUMENT_BULK_EVIDENCE_AND_GLOBAL_GAP_REMEDIATION_DESIGN`

Dort soll auf Basis der tatsächlichen v0.23-Counts entschieden werden, welche
reproduzierbaren Bulk-Security-Type-Quellen für Europa und die übrigen unresolved
Märkte geeignet sind und welche Daten-Remediation-Kandidaten tatsächlich noch aktuell
sind.
