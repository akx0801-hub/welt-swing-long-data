# WELT-SWING LONG DEV — Materialized Official Membership Identity Reconciliation v0.31

**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Stage:** `CURRENT_MASTER_MATERIALIZED_OFFICIAL_MEMBERSHIP_IDENTITY_RECONCILIATION`

## 1. Ausgangslage

v0.30 hat erstmals für ein bislang fehlendes Current-Master-Segment vollständige offizielle Membership-Evidence materialisiert:

- `BR_IBRX100`
- 98 B3-Security-Codes
- offizieller B3-Header: `31/08/26`
- offizielle B3-Quelle: `GetPortfolioDay`
- noch kein Canonical Import

Zusätzlich wurde für Mexiko ein offizielles finales S&P/BMV-IPC-Rebalance-Dokument materialisiert. Dieses Dokument beweist zwei Änderungen, aber nicht die vollständige aktuelle Membership.

## 2. Masterregeln

Der DEV-Master verlangt für Security-Identität:

1. gültige ISIN + Primary MIC + Primary Ticker,
2. oder — falls die offizielle Quelle keine ISIN liefert — Primary MIC + offizieller Primary Ticker/Exchange Code + stabiler WS_ID.

Es ist verboten, eine ISIN zu raten.

Für den Strict-U3K-Instrument-Gate gilt:

PASS:
- COMMON_STOCK
- ORDINARY_SHARE
- eindeutig zulässige Ordinary-Share-Class

FAIL:
- Preferred Shares
- Units
- Fonds / ETF
- Warrants / Rights / Derivate
- sonstige nicht zulässige Instrumente

`UNKNOWN` ist kein Strict-PASS.

## 3. B3 Primary MIC

Für B3 wird `BVMF` verwendet.

Offizielle B3-Dokumentation beschreibt `MarketIdentifierCode` gemäß ISO 10383 und nennt für B3 den Default-Wert `BVMF`.

Evidenz:
`https://www.b3.com.br/lumis/portal/file/fileDownload.jsp?fileId=8AA8D0976133DB2C0161344308732779`

Die v0.30-Membership-Antwort selbst liefert keine ISIN. Deshalb nutzt v0.31 ausschließlich den vom Master ausdrücklich zugelassenen Fallback:

`WS:BVMF:<OFFIZIELLER_B3_TICKER>`

Beispiel:

`WS:BVMF:ABEV3`

Die ISIN bleibt leer.

## 4. B3 Instrument-Semantik

Die offizielle B3-Typbezeichnung wird fail-closed klassifiziert.

### PASS

Typ beginnt mit:

`ON`

→ `ORDINARY_SHARE`

B3 selbst verwendet ON für ações ordinárias (Ordinary Shares).

### FAIL

Typ beginnt mit:

`PN`, `PNA`, `PNB`, `PNC`, ...

→ `PREFERRED_SHARE`

Typ beginnt mit:

`UNT` oder `UNIT`

→ `UNIT`

Preferred Shares und Units sind nach DEV-Master kein Strict-U3K-PASS.

### NOT VERIFIED

Alle anderen Typen werden:

`UNKNOWN / NOT_VERIFIED`

und nicht promoviert.

## 5. Source-AsOf

Die offizielle B3-JSON-Antwort enthält:

`header.date = 31/08/26`

v0.31 speichert dies als:

`Source_AsOf_Official = 2026-08-31`

Die genaue fachliche Bedeutung des B3-Headers wird nicht überinterpretiert. Deshalb:

`Source_AsOf_Semantics = OFFICIAL_B3_HEADER_DATE_UNINTERPRETED`

## 6. Outputs Brasilien

Alle 98 offiziellen Source-Mitglieder bleiben nachvollziehbar erhalten:

- `br_ibrx100_identity_reconciliation_v0.31.csv`

Strict-Ordinary-Kandidaten:

- `br_ibrx100_strict_ordinary_candidates_v0.31.csv`

Master-konforme Instrument-FAILs:

- `br_ibrx100_instrument_exclusions_v0.31.csv`

Nicht eindeutig klassifizierbare Instrumente:

- `br_ibrx100_instrument_not_verified_v0.31.csv`

Wichtig:

`Strict_Ordinary_Identity_Candidate = true`

ist noch **keine Eligibility-Promotion**.

Liquidität, Price/Data-Quality und weitere Eligibility-Gates folgen separat.

## 7. Mexiko

Das eingefrorene BMV-Dokument bestätigt:

- Announcement: 13.03.2026
- effective prior to open: 23.03.2026
- `VOLAR A` — ADD
- `CUERVO *` — DROP

v0.31 erstellt daraus:

`mx_ipc_official_change_ledger_v0.31.csv`

Der Ledger ist ausschließlich Change-Evidence.

Er darf nicht als vollständiger aktueller S&P/BMV-IPC-Bestand ausgegeben werden.

## 8. Keine Current-Master-Mutation

v0.31 darf nicht:

- die 1.535 Current-Master-Zeilen verändern,
- Brasilien bereits kanonisch importieren,
- Mexiko aus einem Change-Dokument rekonstruieren,
- Preferred Shares oder Units als Strict-PASS zulassen,
- ISIN raten,
- Liquiditäts-PASS vergeben,
- Preise laden,
- P0 starten,
- Alpha Vantage verwenden,
- produktive Trading-Autorität erzeugen.

Der Stage ist offline-only.

## 9. Checkpoint-Logik

Für die 98 offiziellen B3-Zeilen:

- `pass_count` = Strict Ordinary Identity Candidates
- `fail_count` = Instrument-FAILs
- `quarantine_count` = Instrument NOT VERIFIED

Der globale Stage-Status bleibt `PARTIAL`, weil das gesamte 14-Segment-Source-Superset noch nicht vollständig ist.

## 10. Current Handoff

Der Stage erzeugt:

- `WELT-SWING-CURRENT-Handoff-v0.31.md`
- `WELT-SWING-CURRENT-Handoff-CURRENT.md`

Der Recovery-Pfad wird damit auf v0.31 fortgeschrieben.

## 11. Nächster Stage

`CURRENT_MASTER_BR_IBRX100_SOURCE_SEGMENT_FREEZE_AND_LIQUIDITY_PRECHECK`

Dort soll:

1. der offizielle 98er B3-Source-Snapshot versioniert eingefroren werden,
2. nur der Ordinary-Share-Subset in den Liquiditäts-/Datenqualitäts-Precheck gehen,
3. kein regionaler Schwellenwert abgesenkt werden,
4. erst nach bestandener Eligibility über eine Aufnahme in `SWING_U3K_ELIGIBLE` entschieden werden.

Der 1.535er Current Master bleibt bis zu einem separaten kontrollierten Import unverändert.
