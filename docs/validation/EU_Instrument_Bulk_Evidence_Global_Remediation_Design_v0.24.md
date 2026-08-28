# WELT-SWING LONG DEV — EU Instrument Bulk Evidence & Global Gap Remediation Design v0.24

**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Stage:** `EU_INSTRUMENT_BULK_EVIDENCE_AND_GLOBAL_GAP_REMEDIATION_DESIGN`

## Zweck

v0.24 setzt unmittelbar auf dem erfolgreichen Root-Cause-Audit v0.23 auf. Der Stage löst noch keine neuen
Instrumententscheidungen aus. Er baut stattdessen die belastbare Route für die 650 verbliebenen
Instrument-Evidence-Fälle und reconciliert die 60 echten Daten-Remediation-Fälle gegen bereits vorhandene
spätere QA-Evidence.

v0.24 ist vollständig offline. Es werden keine externen Quellen neu abgerufen.

## Ausgangslage aus v0.23

650 Instrumenttypen sind noch nicht strikt verifiziert:

- EU_STOXX600: 365
- CA_TSX: 105
- KR_KOSPI200: 92
- HK_HSI: 82
- MX_IPC: 6

Zusätzlich existieren 60 Daten-Remediation-Kandidaten:

- 55 historische Cache-Non-READY-Fälle
- 5 `DATA_OR_FX_NOT_VERIFIED`-Fälle

Die 916 validen Strict-/historischen Ausschlüsse werden nicht zurückgeholt und keine Liquiditätsschwelle wird
zur Verbesserung regionaler Coverage abgesenkt.

## Europa: 365 nach Primärmarkt routen

Die 365 EU-Zeilen werden nach `Country + Primary_MIC` gruppiert. Jede Gruppe erhält ausschließlich eine
**Source-Klasse**, noch keine konkrete ungeprüfte URL:

`OFFICIAL_PRIMARY_EXCHANGE_BULK_SECURITY_REFERENCE`

Erforderlich für eine spätere Klassifikation sind mindestens:

- deterministischer Security-Identifier: Primärbörsen-Code/Ticker oder ISIN,
- Security Type / Share Class oder CFI,
- dokumentierte offizielle Semantik,
- Source-Version oder As-of,
- Raw-Hash,
- exakte Zuordnung zum eingefrorenen `WS_ID`.

Namensmatching und per-security Web-Fanout bleiben verboten. Ambiguität ist fail-closed.

## Hongkong: vorhandene Bulk-Evidence nutzen

v0.9 hat die offizielle HKEX `Full List of Securities` bereits erfolgreich als Bulk-Datei geparst und alle
82 heute noch unresolved HSI-Zeilen exakt gematcht. Die Datei enthält unter anderem:

- `Category`
- `Sub-Category`
- `ISIN`
- Stock Code

v0.24 prüft, dass die 82 eingefrorenen HKEX-Matches exakt dieselben 82 `WS_ID` wie die aktuelle v0.23-HK-Queue
sind und erstellt eine Category/Sub-Category-Inventur.

**Wichtig:** `Category = Equity` wird in v0.24 nicht automatisch als strikter Ordinary-Share-PASS interpretiert.
Dafür fehlt noch die ausdrücklich validierte offizielle Semantik der HKEX-Kategorien. v0.24 ändert daher
0 Instrumententscheidungen.

## Kanada, Korea, Mexiko

Die bisherigen Blocker bleiben sichtbar:

- Kanada: offizielle Semantikvalidierung in v0.14 fehlgeschlagen; kein Blanket-PASS aus TSX-Composite-Mitgliedschaft.
- Korea: offizieller KRX-Bulk-Transport scheiterte in v0.9/v0.10 mit HTTP 400; die Request-Form muss sauber
  aufgelöst werden.
- Mexiko: v0.9 materialisierte nur eine HTML-Capability-Probe; für die sechs Titel fehlt weiterhin eine
  offizielle maschinenlesbare oder eindeutig klassifizierende Security-Type-Evidence.

## Daten-Remediation

v0.24 überprüft eine wichtige Lineage-Eigenschaft: Die 55 v0.23-`DATA_HISTORY_REMEDIATION_CANDIDATE`-IDs
müssen exakt den 55 `residual_non_ready_v0.4`-IDs des bereits promovierten QA-Bar-Policy-Laufs entsprechen.
Damit wird verhindert, dass alte Cache-Zustände und spätere QA-Policy-Stände miteinander vermischt werden.

Die fünf `DATA_OR_FX_VERIFICATION_CANDIDATE`-Zeilen werden separat für eine erneute Liquiditäts-/Coverage-
Berechnung vorgemerkt. Auch hier erfolgt in v0.24 keine Eligibility-Promotion.

## Bounded-Network-Policy für den nächsten Stage

Der nächste Stage darf Netzwerkzugriffe nur als begrenzte Bulk-Probes einsetzen. Verboten bleiben:

- 650 oder 365 Einzelrequests,
- Company-Name-Guessing,
- Alpha Vantage,
- unversionierte Security-Type-Labels,
- stilles Mischen unterschiedlicher Klassifikationssysteme,
- PASS allein aus Indexmitgliedschaft, sofern die offizielle Indexregel nicht selbst als ausreichender
  Common-/Ordinary-Share-Nachweis validiert wurde.

## Outputs

- `eu_unresolved_route_inventory_v0.24.csv`
- `global_instrument_evidence_route_inventory_v0.24.csv`
- `hkex_frozen_semantics_inventory_v0.24.csv`
- `data_remediation_reconciliation_v0.24.csv`
- `data_remediation_counts_v0.24.csv`
- `global_remediation_priority_v0.24.csv`
- `bounded_probe_policy_v0.24.json`
- `summary_v0.24.json`
- `stage_checkpoint_v0.24.json`
- `manifest_v0.24.json`

## Governance

v0.24 führt ausnahmslos aus:

- 0 externe Requests
- 0 neue Instrument PASS/FAIL
- 0 Eligibility-Promotions
- 0 neue Kurs-/FX-Downloads
- 0 Sector RS
- 0 P0-Entscheidungen
- 0 produktive Trading-Autorität
- keine Mutation des kanonischen Masters
- keine Mutation historischer Artefakte

Das globale Gate bleibt:

`BLOCKED_RESEARCH_PARTIAL_NOT_GLOBAL_STRICT`

## Nächster Stage

`OFFICIAL_BULK_SECURITY_TYPE_PROBE_AND_DATA_GAP_RECHECK`

Er darf die in v0.24 freigegebene Bounded-Bulk-Policy verwenden. Erst wenn eine Quelle, ihr Schema, ihre
Semantik und das exakte Mapping auditiert sind, darf ein nachfolgender Klassifikationsstage neue
Instrumententscheidungen erzeugen.
