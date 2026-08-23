# Welt-Swing Long DEV — Identity + Provider Remediation v0.2

**Ausgangslage:** Full Identity Provider Audit v0.1  
**Input:** 3.664 Securities / 14 Segmente  
**v0.1 Provider-Mapping:** 3.491 / 3.664 = 95,2784 %  
**v0.1 unresolved:** 173  
**Produktiv:** nein  
**P0:** aus  
**Alpha Vantage:** verboten  
**Preis-/OHLCV-Lauf:** nein

## Ziel

v0.2 ist die gezielte Remediation der im v0.1-Audit verbliebenen Probleme.
Sie ändert nicht die Trading-Strategie und führt keinen Preisrun aus.

## Remediation-Blöcke

### Kanada

`WS:XTSE:NA` wird deterministisch auf `NA.TO` gesetzt. Der kanonische WS_ID und
der MIC `XTSE` liefern zusammen den eindeutigen legitimen Ticker `NA`.

### Mexiko

Die offizielle Indexnotation enthält Share-Class-Bezeichnungen mit Leerzeichen,
z. B. `GFNORTE O`, `CEMEX CPO`, `FEMSA UBD` und `GAP B`.
Yahoo verwendet für diese Titel kompakte Provider-Symbole wie
`GFNORTEO.MX`, `CEMEXCPO.MX`, `FEMSAUBD.MX`.

v0.2 entfernt Leerzeichen/Index-Sterne nur als **Kandidatenregel**. Ein Kandidat
wird erst übernommen, wenn Yahoo Search den exakten Equity-Symboltreffer oder
einen eindeutigen Treffer am erwarteten Mexico-Markt bestätigt.

### Europa

v0.1 hat viele richtige Unternehmensnamen gefunden, sie wegen Cross-Venue-
Mehrdeutigkeit aber nicht automatisch übernommen. v0.2 filtert zuerst auf den
für den MIC erwarteten Yahoo-Marktsuffix (`.PA`, `.DE`, `.AS`, `.ST`, `.CO` usw.).

Bei Stockholm und Kopenhagen wird zusätzlich die typische Reuters/RIC-
Share-Class-Schreibweise nur als Ranking-Hinweis verwendet:

- `ASSAb.ST` → Kandidatenhinweis `ASSA-B`
- `ATCOa.ST` → `ATCO-A`
- `CARLb.CO` → `CARL-B`

Kein Treffer wird allein aus dieser Syntax erfunden.

### Südafrika / JSE

Alle 40 JSE-Namen werden erneut geprüft, auch die 20 provisorischen
`SEARCH_HIGH_CONFIDENCE`-Treffer aus v0.1.

Nur ein **eindeutiger** `.JO`-Equity-Treffer wird promoted. Gibt es mehrere
glaubwürdige JSE-Securities desselben Unternehmens, bleibt der Fall Review.
Damit wird insbesondere verhindert, dass eine Sonder-Share-Class nur wegen
des Firmennamens als gewöhnliche Aktie übernommen wird.

### Duplicate-/Cross-Listing-Logik

v0.1 hat `group` und `holdings` bei der Namensnormalisierung zu aggressiv
entfernt. v0.2 behält diese wirtschaftlich relevanten Begriffe bei.

Mehrfachnotierungen an verschiedenen Börsen werden künftig als
`CROSS_LISTING_OR_DUAL_LISTING_NON_BLOCKING` klassifiziert und nicht gelöscht.

Nur gleichnamige Securities am **gleichen Venue** bleiben als
`SAME_VENUE_POSSIBLE_DUPLICATE_REVIEW` blockierend.

## Outputs

- `universe/Welt-Swing-Universe-Master-Remediated-v0.5.csv`
- `universe/Welt-Swing-Universe-Master-Remediated-v0.5.xlsx`
- `output_identity_remediation/summary_v0.2.json`
- `output_identity_remediation/remediation_audit_v0.2.csv`
- `output_identity_remediation/review_queue_v0.2.csv`
- `output_identity_remediation/cross_listing_candidates_v0.2.csv`
- `output_identity_remediation/same_venue_duplicate_review_v0.2.csv`
- `output_identity_remediation/proposed_yahoo_overrides_v0.2.csv`

Die vorgeschlagenen Yahoo-Overrides werden **nicht automatisch** in
`config/yahoo_symbol_overrides.csv` geschrieben. Erst nach Prüfung des
Remediation-Ergebnisses wird entschieden, welche Mapping-Änderungen endgültig
promoted werden.

Ein neuer 3.664er Preisrun bleibt bis dahin gesperrt.
