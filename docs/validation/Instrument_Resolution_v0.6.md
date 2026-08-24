# Welt-Swing Long DEV — Instrument Resolution v0.6

## Zweck

v0.6 bearbeitet **nur** die 2.113 Instrument-Review-Fälle aus dem bereits
abgeschlossenen U3K Liquidity / FX Audit v0.5. Die restlichen 3.657 aktiven
Universe-Zeilen werden nicht neu recherchiert und der kanonische Master wird
nicht verändert.

Die Regel folgt dem Swing-Long-DEV-v0.1-Instrument-Gate:

- PASS: `COMMON_STOCK`, `ORDINARY_SHARE`, eindeutig zulässige Ordinary-Share-Class.
- FAIL: Preferred Shares, Fonds, ETF, Units, Warrants, Rights, Derivate,
  unauflösbare Depositary-Strukturen und andere eindeutig ungeeignete
  Instrumente.
- UNKNOWN / nicht verifiziert ist im Strict Universe **kein PASS**.

## Gruppenregel v0.6

Nur **US_SP1500** erhält einen automatischen Gruppen-PASS.

Begründung: Die offizielle S&P-U.S.-Indices-Methodik beschreibt die Familie als
US-Aktienindizes und den breiten U.S.-Markt als alle zulässigen US Common
Equities. Der eingefrorene S&P Composite 1500 besteht aus S&P 500, MidCap 400
und SmallCap 600. Für DEV v0.6 wird diese offizielle Index-Family-Evidenz als
hinreichender gruppenweiser Nachweis für `COMMON_STOCK` akzeptiert.

Quelle:
https://www.spglobal.com/spdji/en/methodology/article/sp-us-indices-methodology/

Erwarteter Gruppen-PASS aus der v0.5-Review-Queue: **1.332 Zeilen**.

## Warum die anderen Märkte nicht pauschal freigegeben werden

### Kanada — CA_TSX

Die offizielle S&P/TSX-Methodik sagt ausdrücklich, dass der Composite sowohl
Common Stocks als auch Income Trust Units enthält. Ein Blanket-PASS wäre damit
fachlich falsch.

Quelle:
https://www.spglobal.com/spdji/en/methodology/article/sp-tsx-canadian-indices-methodology/

### Australien — AU_ASX200

Der offizielle S&P/ASX-200-Auftritt spricht zwar von index-eligible stocks,
offizielle Indexmitteilungen zeigen aber auch REIT-Konstituenten. Deshalb kein
pauschaler Ordinary-Share-PASS.

Quelle:
https://www.spglobal.com/spdji/en/indices/equity/sp-asx-200/

### Mexiko — MX_IPC

Die offizielle IPC-Konstituentendarstellung enthält unter anderem CPO-Strukturen.
Indexmitgliedschaft allein beweist daher keine Ordinary Share.

Quelle:
https://www.spglobal.com/spdji/en/indices/equity/sp-bmv-ipc/

### Neuseeland — NZ_NZX50

Die offizielle Seite spricht von eligible stocks. Für das strikte DEV-Instrument-
Gate ist das allein noch keine positive Ordinary/Common-Share-Verifikation.

Quelle:
https://www.spglobal.com/spdji/en/indices/equity/sp-nzx-50-index/

### Europa, Hongkong, Korea, Südafrika, Brasilien

Für v0.6 wird aus der aktuellen Gruppen-Evidenz **kein** Blanket-PASS abgeleitet.
Diese Segmente bleiben gezielte Review-Märkte. Damit wird vermieden, dass
Indexmitgliedschaft stillschweigend einen nicht verifizierten Instrumenttyp
überschreibt.

## Automatische FAIL-Regeln

Nur klare Strukturhinweise werden automatisch abgelehnt, zum Beispiel:

- ETF / Preferred / Warrant / Rights / ADR / GDR,
- kanadische REIT-/Income-Trust-/Unit-Kennzeichen,
- australische explizite REIT-/Stapled-/Unit-Kennzeichen,
- mexikanische CPO-/FIBRA-Kennzeichen,
- Hongkong-REIT-/Trust-Unit-Kennzeichen,
- eindeutige NZ Trust-Unit-/Property-Fund-Kennzeichen.

Unsichere Fälle werden **nicht geraten**, sondern bleiben `NOT_VERIFIED`.

## Output

Der Lauf erzeugt:

- `output_instrument_resolution_v0_6/summary_v0.6.json`
- `instrument_resolution_overlay_v0.6.csv`
- `instrument_auto_pass_v0.6.csv`
- `instrument_auto_fail_v0.6.csv`
- `instrument_manual_review_queue_v0.6.csv`
- `eligibility_after_instrument_v0.6.csv`
- `strict_u3k_candidate_after_instrument_v0.6.csv`
- `instrument_resolution_by_segment_v0.6.csv`

Der kanonische Universe-Master bleibt unverändert. Das Overlay ist die einzige
neue Instrument-Evidenzschicht.

## Erwarteter Effekt

Der größte offene Block wird ohne 2.113 Einzelabfragen reduziert:

- bisheriger expliziter Strict-PASS: 597,
- US-SP1500-Gruppen-PASS: 1.332,
- damit mindestens 1.929 Strict-Kandidaten vor den verbleibenden Markt-Reviews,
  sofern kein anderes Gate FAIL ist.

Die tatsächliche Zahl wird ausschließlich aus dem Lauf übernommen.

## Governance

- keine Aktienkursdownloads,
- keine FX-Downloads,
- keine per-Security-Webcalls,
- kein Alpha Vantage,
- kein Paid Provider,
- kein P0,
- keine produktive Handelsfreigabe,
- kein Strict-U3K-Freeze solange `manual_review_rows > 0`.

Der nächste Schritt nach v0.6 ist nur die verbleibende Review-Queue, nach Markt
gebündelt und mit offizieller bzw. Primärbörsen-Evidenz. Es wird nicht wieder das
gesamte Universe untersucht.
