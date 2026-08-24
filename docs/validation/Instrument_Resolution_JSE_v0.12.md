# Welt-Swing Long DEV — Instrument Resolution JSE v0.12

## Zweck

v0.12 ist die deterministische Klassifikationsstufe für die **17** noch offenen `ZA_TOP40`-Zeilen.

Sie baut ausschließlich auf:
- dem erfolgreichen offiziellen JSE-Bulk-Probe v0.11,
- dem aktuellen öffentlichen `isinfull_e.zip`,
- der JSE-Dokumentation zu Instrument Types,
- und den eingefrorenen v0.10/v0.11 Inputs auf.

## Ausgangslage

v0.11 hat die JSE-Quelle erfolgreich materialisiert:

- JSE Folder HTTP 200
- ZIP HTTP 200
- genau ein `isinfull_e.zip`
- genau ein Archivmitglied
- 2 externe Requests
- 0 Eligibility-Entscheidungen
- 667 offene Instrumentfälle
- 2.020 Strict Candidates

## Aktuelle JSE-Datenstruktur

Die aktuelle öffentliche Datei wird in v0.12 nur dann verwendet, wenn die Fixed-Width-Struktur vollständig strukturell validiert.

Die v0.11-Stichprobe zeigt einen 277-Zeichen-Datensatz mit u. a.:

- ISIN
- Issuer Name
- Issue Description
- Number of Securities
- Nominal Value
- Currency
- **Instrument Type**
- **Alpha Code**
- Instrument Version
- Issuer Registration Number

v0.12 prüft die Record-Länge und die strukturelle Gültigkeit von ISIN, Currency, Version und Alpha Code über den gesamten Bulk-Datensatz, bevor irgendeine Klassifikation zulässig ist.

## Identitätsauflösung

Die 17 ZA-Zeilen besitzen im aktuellen Canonical Input kein `Primary_Ticker`.

Daher wird der bereits eingefrorene `Yahoo_Symbol` ausschließlich als Lookup-Key verwendet:

`XYZ.JO → XYZ`

Ein Instrument wird nur bei exaktem Match gegen den offiziellen `JSE_Alpha_Code` verwendet.

Bei Mehrdeutigkeit oder fehlendem exakten Match bleibt die Zeile `NOT_VERIFIED`.

## Instrument-Type-Regeln

Strict PASS:

- `Aord` — A Ordinary Share
- `Bord` — B Ordinary Share
- `Nord` — N Ordinary
- `Ordinary` — Ordinary Share

Strict FAIL bei klar nicht-gewöhnlichen Instrumenten, darunter:

- `DepRec` — Depository Receipts
- `ETF`
- `LU` — Linked Unit
- `PS` — Preference Shares
- `UT` — Unit Trusts
- `PL` — Participatory Interest
- Debentures / warrants / options / paid letters / ähnliche Sonderstrukturen

`Securities` oder unbekannte Codes bleiben `NOT_VERIFIED`.

## Fail-Closed

Wenn:

- ZIP nicht erreichbar,
- Fixed-Width-Layout nicht valide,
- Alpha-Match nicht eindeutig,
- oder Instrument Type nicht deterministisch klassifizierbar,

gibt es keinen PASS aus Vermutung.

## Governance

Unverändert:

- Alpha Vantage verboten
- keine Preisdownloads
- keine FX-Downloads
- keine per-Security-Webcalls
- P0 aus
- keine produktive Trading Authority
- Canonical Master unverändert
