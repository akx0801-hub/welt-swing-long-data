# Welt-Swing Long DEV — Instrument Resolution Primary-Market Bundle v0.9

## Status / Zweck

v0.9 ist bewusst **keine neue Klassifikationsrunde**, sondern eine gebündelte Primärmarkt-Evidenzprobe auf der eingefrorenen v0.8-Restqueue.

Frozen Source v0.8:
- Manual Review: 667
- Strict candidates: 2020
- Restsegmente: CA 105 / EU 365 / HK 82 / KR 92 / MX 6 / ZA 17
- Strict freeze: weiterhin nicht zulässig

## Design

Maximal ein offizieller Börsen-/Primärmarkt-Request je Restmarkt, insgesamt höchstens sechs Requests. Keine per-Security-Webcalls.

- Canada: TMX/TSX Listed Company Directory — Bulk-/Download-Fähigkeit entdecken.
- Europe: STOXX Europe 600 Data/Reference Data — maschinenlesbare Komponenten-/Referenzquelle entdecken.
- Hong Kong: HKEX Full List of Securities — XLSX einmalig laden und die 82 Zielcodes exakt matchen.
- South Korea: KRX Data Marketplace `전종목 기본정보` — ein Bulk-POST und die 92 sechsstelligen Zielcodes matchen.
- Mexico: BMV Empresas Listadas — Bulk-/Download-Fähigkeit entdecken.
- South Africa: JSE Reference Data — öffentlichen Bulk-Zugang bzw. Referenzpfad entdecken.

## Entscheidungsgrenze

v0.9 ändert **keine** PASS/FAIL-Entscheidung. `decisions_changed = 0` ist ein hartes Gate.

Grund:
- Indexmitgliedschaft allein beweist nicht zwingend `common/ordinary share`.
- HKEX `Equity` umfasst neben Ordinary Shares auch Preference Shares.
- KRX-Grunddaten müssen zuerst auf tatsächlich security-typspezifische Felder geprüft werden.
- Mexico enthält gemischte Share-/Certificate-Strukturen (u. a. CPO).
- Canada, Europe und South Africa benötigen weiterhin explizite, maschinenlesbare Security-Type-Evidenz.

## Outputs

`output_instrument_resolution_v0_9/`
- `summary_v0.9.json`
- `source_probe_status_v0.9.csv`
- `target_counts_v0.9.csv`
- `instrument_manual_review_queue_v0.9.csv`
- `hkex_reference_matches_v0.9.csv`
- `krx_reference_matches_v0.9.csv`
- `discovered_bulk_links_v0.9.csv`

## Governance

Unverändert:
- kein P0
- keine produktive Trading Authority
- kein Alpha Vantage
- keine Preisdownloads
- keine FX-Downloads
- keine per-Security-Webcalls
- kein Paid Provider
- Canonical Master unverändert
- Strict freeze bleibt gesperrt

## Nächster DEV-Schritt nach erfolgreichem v0.9-Run

Die tatsächlich gelieferten HKEX-/KRX-Felder und die entdeckten Bulk-Links werden ausgewertet. Erst danach entsteht v0.10 als deterministische Klassifikationsstufe. Positive Entscheidungen dürfen nur aus security-spezifischen Feldern mit dokumentierter offizieller Semantik abgeleitet werden.
