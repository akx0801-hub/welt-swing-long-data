# Welt-Swing Long DEV — Full Identity + Provider Mapping Audit v0.1

**Scope:** kompletter 3.664er 14-Segmente-Source-Master  
**Produktiv:** nein  
**P0:** aus  
**Alpha Vantage:** verboten  
**Neuer Preis-/OHLCV-Lauf:** nein

## Zweck

Dieser Audit ist der One-shot-Schritt nach `COMPLETE_SOURCE_SUPERSET`.

Er prüft alle 3.664 Source-Securities in einem Lauf und trennt dabei:

- kanonische Source-Identität,
- Yahoo-Provider-Symbol,
- bekannte Mappingfehler aus dem 1.535er Diagnoselauf,
- neue Source-Segmente,
- temporäre Name-only-Identitäten,
- mögliche Dubletten,
- unresolved / review-required Fälle.

## Mapping-Reihenfolge

1. Projekt-Overrides.
2. Bereits explizit im Master vorhandene Yahoo-Symbole.
3. Gefrorene deterministische MIC-/Suffix-Regeln aus `price_cache.py`.
4. US-SP1500-Source-Ticker direkt mit Yahoo-Share-Class-Normalisierung.
5. Targeted Yahoo Search nur für problematische/unaufgelöste Fälle.
6. Ambige Suchtreffer bleiben im Review-Queue; sie werden nicht automatisch promoted.

Der bestehende 1.535er Diagnoselauf wird als Targeting-Signal verwendet:
`DOWNLOAD_FAILED` und `MAPPING_PENDING` werden gezielt neu aufgelöst.

## Keine Preisabfrage

Der Audit enthält absichtlich weder `yf.download()` noch `.history()`.
Er erzeugt keine OHLCV-, Ranking-, P0-, News-, Sizing- oder Kaufentscheidung.

## Outputs

- `universe/Welt-Swing-Universe-Master-Audited-v0.4.csv`
- `universe/Welt-Swing-Universe-Master-Audited-v0.4.xlsx`
- `output_identity_audit/summary_v0.1.json`
- `output_identity_audit/mapping_audit_v0.1.csv`
- `output_identity_audit/review_queue_v0.1.csv`
- `output_identity_audit/duplicate_review_v0.1.csv`
- `output_identity_audit/search_cache_snapshot_v0.1.jsonl`

`AUDIT_COMPLETE_WITH_REVIEW_QUEUE` ist ein regulärer technischer Erfolg:
Alle 3.664 Zeilen wurden geprüft, aber einzelne Identitäten oder Provider-Mappings
benötigen noch explizite Review. Erst danach wird über einen neuen Gesamt-Preisrun
entschieden.
