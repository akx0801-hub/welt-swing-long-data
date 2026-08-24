# Welt-Swing Long DEV — Instrument Resolution Market Codes v0.7

## Ausgangslage

Nach v0.6 sind noch 778 Instrumentfälle `NOT_VERIFIED`.

v0.7 arbeitet nur auf dieser Restmenge. Ziel ist nicht, neue weiche
Gruppenannahmen einzuführen, sondern ausschließlich solche Fälle zu lösen, für
die offizielle Markt-Codierung oder explizite Security-Struktur einen
deterministischen Entscheid erlaubt.

## Brasilien / IBrX 100

Der IBrX-100-Methodik zufolge kann der Index Aktien und Units enthalten.

B3 dokumentiert für Aktien:

- `XXXX3` = ordinary stock
- `XXXX4` = preferred stock
- `XXXX5` bis `XXXX8` = preferred share classes

B3 dokumentiert für Units:

- `XXXX11` = securities deposit certificate / Unit

Für Swing Long Strict U3K bedeutet das:

- Suffix `3` → PASS
- Suffix `4–8` → FAIL
- Suffix `11` → FAIL

Alle 48 noch offenen BR_IBRX100-Zeilen müssen in v0.7 durch diese Regel
aufgelöst werden. Bleibt auch nur eine brasilianische Zeile ungelöst, stoppt der
Workflow.

Offizielle Quellen:

- B3 Stocks:
  https://www.b3.com.br/en_us/products-and-services/trading/equities/stocks.htm
- B3 Units:
  https://www.b3.com.br/en_us/products-and-services/trading/equities/securities-deposit-certificate-units.htm
- IBrX 100 Methodology:
  https://www.b3.com.br/data/files/A5/61/8B/BB/E6D947102255C247AC094EA8/IBXX-Metodologia-en-us__Modelo_Novo_.pdf

## Kanada

S&P beschreibt den S&P/TSX Composite ausdrücklich als Mischung aus Common
Stocks und Income Trust Units.

Daher gibt es weiterhin **keinen Blanket-PASS** für Kanada.

v0.7 lehnt nur explizite Trust-/REIT-Unit-Fälle mit klarer Namens- und
Symbolstruktur automatisch ab. Der übrige kanadische Rest bleibt
`NOT_VERIFIED`.

Quelle:
https://www.spglobal.com/spdji/en/methodology/article/sp-tsx-canadian-indices-methodology/

## Australien

S&P bezeichnet den ASX 200 als Index eligible stocks. ASX dokumentiert jedoch,
dass viele A-REITs Stapled Securities aus Unternehmensanteil und Trust Unit
sind.

Deshalb bleibt ein Blanket-PASS unzulässig. Nur explizite REIT-/Property-Trust-
Namen werden in v0.7 automatisch FAIL.

Quelle:
https://www.asx.com.au/content/dam/asx/investors/investment-tools-and-resources/understanding-asx-investment-products-for-advisers.pdf

## Hongkong

Hang Seng dokumentiert REITs als eigene Security-Struktur innerhalb seiner
Indexfamilie. Deshalb wird auch hier kein Blanket-PASS eingeführt.

Explizite `REIT`-Namen werden FAIL; alles andere bleibt für die nächste
Primärmarkt-/Security-Level-Runde offen.

## Nicht automatisch entschieden

v0.7 führt bewusst keinen neuen Gruppen-PASS für folgende Restmärkte ein:

- STOXX Europe 600
- KOSPI 200
- Hang Seng Index (außer explizite REITs)
- ASX 200 (außer explizite REIT/Trust-Fälle)
- TSX (außer explizite Trust Units)
- Mexico IPC
- FTSE/JSE Top 40

Unbekannt bleibt unbekannt. Das ist Absicht.

## Outputs

- `output_instrument_resolution_v0_7/summary_v0.7.json`
- `instrument_market_code_overlay_v0.7.csv`
- `instrument_new_pass_v0.7.csv`
- `instrument_new_fail_v0.7.csv`
- `instrument_manual_review_queue_v0.7.csv`
- `eligibility_after_instrument_v0.7.csv`
- `strict_u3k_candidate_after_instrument_v0.7.csv`
- `instrument_resolution_by_segment_v0.7.csv`

## Governance

- nur die 778 v0.6-Restfälle
- keine Aktienkursdownloads
- keine FX-Downloads
- keine Einzel-Webabfragen
- kein Alpha Vantage
- kein Paid Provider
- kein P0
- kein produktiver Trade-Status
- kein Strict-U3K-Freeze solange `remaining_manual_rows > 0`
