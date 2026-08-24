# Welt-Swing Long DEV — Instrument Resolution Primary Market v0.7

## Ausgangspunkt

v0.7 startet ausschließlich vom verifizierten Ergebnis von v0.6:

- 2.113 ursprüngliche Instrument-Review-Fälle,
- 1.332 US-SP1500 Gruppen-PASS,
- 3 automatische FAIL,
- 778 weiterhin `NOT_VERIFIED`,
- 1.929 Strict-Kandidaten,
- Strict-U3K-Freeze weiterhin gesperrt.

v0.7 untersucht **nicht** wieder das gesamte Universe.

## Teil A — Brasilien vollständig über offizielle B3-Codierung

Die B3 veröffentlicht im aktuellen Trading Operational Procedures Manual die
Bedeutung der numerischen Endung des Cash-Market-Tickers.

Für den Strict-Instrument-Gate wird in v0.7 exakt umgesetzt:

- `03` → ordinary shares → **PASS**
- `01–02` → subscription rights → **FAIL**
- `04–08` → preferred shares / preferred classes → **FAIL**
- `09–10` → subscription receipts → **FAIL**
- `11–30` → other assets, darunter Units/Fundanteile → **FAIL**
- `31–40` → BDR-Strukturen → **FAIL**

Offizielle Quelle:
https://sistemasweb.b3.com.br/normativos/MPODENEGOCIACAO20260525.pdf

Damit können die **48** verbleibenden `BR_IBRX100`-Fälle ohne
Security-Level-Webabfragen vollständig klassifiziert werden.

Der Workflow bricht ab, falls auch nur eine der 48 eingefrorenen
Brasilien-Zeilen nicht durch die offizielle B3-Endungsregel aufgelöst werden
kann.

## Teil B — Australien: erst offizielle Bulk-Referenz prüfen

Australien wird in v0.7 **noch nicht** gruppenweise freigegeben.

Die aktuelle S&P/ASX-Methodik sagt ausdrücklich, dass Indexkonstituenten aus
ordinary **und preferred equity stocks** gezogen werden. Außerdem sind Equity-
und Mortgage-REITs indexfähig. ASX-200-Mitgliedschaft allein ist daher kein
strikter Ordinary-Share-Nachweis.

Offizielle Methodik:
https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-asx-australian-indices.pdf

ASX ist zugleich die australische National Numbering Agency und stellt eine
vollständige, monatlich aktualisierte ISIN-Exceldatei für ASX-gelistete
Unternehmen bereit.

Offizielle Seite:
https://www.asx.com.au/markets/market-resources/isin-services

Direkte Bulk-Datei:
https://www.asx.com.au/content/dam/asx/issuers/ISIN.xls

v0.7 lädt diese Datei **genau einmal** und erzeugt nur einen Referenzdaten-Audit:

- Workbook-Sheets,
- tatsächliche Spaltennamen,
- Kandidaten für die ASX-Code-Spalte,
- Match-Coverage der 63 offenen ASX-200-Codes,
- alle offiziellen Felder der gematchten Zeilen.

Es erfolgt in v0.7 **keine automatische ASX-Promotion** aus einer vorab
angenommenen Excel-Struktur. Erst das tatsächlich gelieferte Schema entscheidet,
ob v0.8 daraus belastbar `ORDINARY`, `PREFERENCE`, `UNIT`, `REIT`, `CDI` usw.
ableiten kann.

Falls der ASX-Download oder das XLS-Parsing in GitHub Actions scheitert, wird
dies als Probe-Ergebnis dokumentiert. Die unabhängige B3-Auflösung bleibt
trotzdem verwertbar.

## Erwarteter Stand nach v0.7

Da alle 48 Brasilien-Fälle deterministisch aufgelöst werden müssen:

- Review vor v0.7: 778
- Brasilien aufgelöst: 48
- Review nach v0.7: **730**

Die Zahl der zusätzlichen PASS-Titel aus Brasilien wird nicht vorweggenommen,
sondern aus dem Lauf übernommen.

## Outputs

- `output_instrument_resolution_v0_7/summary_v0.7.json`
- `b3_instrument_resolution_v0.7.csv`
- `instrument_manual_review_queue_v0.7.csv`
- `eligibility_after_instrument_v0.7.csv`
- `strict_u3k_candidate_after_instrument_v0.7.csv`
- `remaining_review_by_segment_v0.7.csv`
- `asx_reference_probe_v0.7.json`
- bei erfolgreichem ASX-Parsing zusätzlich:
  - `asx_reference_workbook_schema_v0.7.csv`
  - `asx_reference_code_column_candidates_v0.7.csv`
  - `asx_reference_matches_v0.7.csv`

Die heruntergeladene ASX-XLS-Datei wird nur als kurzlebiges Workflow-Artefakt
aufbewahrt und nicht als neue kanonische Universe-Quelle committed.

## Governance

- keine Aktienkursdownloads,
- keine FX-Downloads,
- maximal **eine** externe Bulk-Referenzanfrage (ASX),
- keine Webabfrage pro Security,
- kein Alpha Vantage,
- kein Paid Provider,
- keine Mutation des kanonischen Universe-Masters,
- kein P0,
- keine produktive Handelsfreigabe,
- kein Strict-U3K-Freeze solange noch `NOT_VERIFIED` vorhanden ist.

Der nächste Schritt wird erst nach dem tatsächlichen ASX-Probe-Ergebnis
festgelegt. Damit wird nicht geraten, welche Informationen die offizielle
Exceldatei enthält.
