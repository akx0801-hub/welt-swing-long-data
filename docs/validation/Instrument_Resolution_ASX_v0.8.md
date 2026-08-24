# Welt-Swing Long DEV — Instrument Resolution ASX v0.8

## Warum v0.8 statt des neu hochgeladenen Market-Codes-v0.7-Laufs

Im Repository existiert bereits ein **erfolgreicher Primary-Market-v0.7-Lauf**.
Er hat alle 48 brasilianischen Restfälle aufgelöst und zugleich die offizielle
ASX-ISIN-Referenz einmalig geladen und für alle 63 australischen Resttitel
vollständig gematcht.

Der danach hochgeladene Workflow `Instrument Resolution Market Codes v0.7`
startet dagegen erneut von der alten v0.6-Queue mit 778 Fällen und schreibt in
dasselbe `output_instrument_resolution_v0_7`-Verzeichnis. Er wird deshalb **nicht
mehr ausgeführt**. Sonst könnte der bereits bessere v0.7-Stand überschrieben
werden.

v0.8 baut ausschließlich auf dem bereits erfolgreich eingefrorenen v0.7-Stand
auf.

## Eingefrorener v0.7-Stand

- manuelle Restfälle: 730
- Strict-Kandidaten: 1.967
- Brasilien: 38 PASS, 10 FAIL, 0 unresolved
- Australien im Rest: 63
- offizielle ASX-Referenz-Matches: 63/63
- ASX-Referenzabdeckung: 100 %

## Offizielle ASX-Evidenz

Quelle der bereits eingefrorenen Referenz:

`https://www.asx.com.au/content/dam/asx/issuers/ISIN.xls`

Die v0.7-Ausgabe enthält für alle 63 ASX-Zielcodes die offiziellen Spalten:

- ASX code
- Company name
- Security type
- ISIN code

v0.8 macht **keinen neuen Webrequest**. Es verwendet ausschließlich die bereits
im Repository gespeicherte Datei
`output_instrument_resolution_v0_7/asx_reference_matches_v0.7.csv`.

## Deterministische ASX-Regel

### PASS

Exakt:

`ORDINARY FULLY PAID`

Das ist eine positive Primärmarkt-Verifikation einer Ordinary Share und erfüllt
das Strict-U3K-Instrument-Gate.

### FAIL

Security Types mit:

- `FULLY PAID ORDINARY/UNITS STAPLED SECURITIES`
- `CDI ...`
- `CHESS DEPOSITARY INTERESTS ...`

Stapled Securities enthalten eine Unit-Komponente. CDI/CHESS-Depositary-
Interests sind Depositary-Strukturen und keine direkt verifizierte
Common/Ordinary Share auf dem betrachteten Primärlisting. Beide sind außerhalb
des strikten Common-/Ordinary-Share-Gates.

## Erwartete exakte Auflösung

Aus den 63 offiziellen ASX-Matches ergeben sich:

- 53 PASS `ORDINARY FULLY PAID`
- 5 FAIL Stapled Ordinary/Units
- 5 FAIL CDI/CHESS Depositary Interests
- 0 unresolved

Damit:

- Restqueue 730 → 667
- Strict-Kandidaten 1.967 → 2.020

Diese Zahlen sind harte Workflow-Gates. Eine Abweichung stoppt den Lauf.

## Schutz vor Versionsregression

Der Workflow prüft die Git-Blob-SHAs der vier bereits erfolgreichen v0.7-
Quellen vor der Ausführung. Dadurch bricht v0.8 ab, falls der alte v0.7-Stand
zwischenzeitlich überschrieben wurde.

## Governance

- keine Aktienkursdownloads
- keine FX-Downloads
- keine per-Security-Webcalls
- keine neue externe Referenzabfrage
- kein Alpha Vantage
- kein Paid Provider
- kein P0
- keine produktive Handelsfreigabe
- kanonischer Universe-Master bleibt unverändert
- kein Strict-U3K-Freeze solange die Restqueue nicht 0 ist

Nach v0.8 bleiben nur noch Kanada, Europa, Hongkong, Korea, Mexiko und Südafrika
für die nächste gebündelte Primärmarkt-Runde übrig.
