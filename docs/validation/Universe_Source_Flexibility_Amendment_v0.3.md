# Welt-Swing Long DEV — Universe Source Flexibility Amendment v0.3

**Freigabe:** 2026-08-23  
**Status:** APPROVED  
**Geltungsbereich:** Universe-/Membership- und Identity-Vorbereitung  
**Produktive Trading-Autorität:** NEIN  
**P0:** AUS  
**Alpha Vantage:** VERBOTEN

## 1. Freigegebene Änderung

Für die Vervollständigung des Welt-Swing-Source-Universums ist die exakte Herkunft
einer Constituents-Liste nicht mehr das primäre Gate. Entscheidend sind künftig:

1. vollständige und nachvollziehbare Abdeckung des vorgesehenen Markt-/Indexsegments,
2. ein öffentlich bzw. frei zugänglicher und automatisierbarer Datenpfad,
3. Speicherung von Source-ID, URL und Abrufzeitpunkt,
4. Count-/Plausibilitätsprüfung,
5. spätere gemeinsame Identity- und Provider-Mapping-Prüfung über den vollständigen Master.

Offizielle Indexanbieter bleiben bevorzugte Quellen, sind aber **keine notwendige
Voraussetzung mehr**, wenn vollständige frei zugängliche Alternativen vorhanden sind.

## 2. Konsequenz für Phase 2

Die bisher fehlenden Segmente werden jetzt als Source-Superset aufgenommen:

- US_SP1500
- KR_KOSPI200
- AU_ASX200
- NZ_NZX50
- MX_IPC
- BR_IBRX100
- ZA_TOP40

Zusammen mit den bereits eingefrorenen sieben Segmenten entsteht damit ein
14-Segmente-Source-Superset.

## 3. Trennung der Qualitätsstufen

**Source-Superset COMPLETE** bedeutet nur:
- das Segment ist aufgenommen,
- Ticker/Name bzw. eine ausreichende Source-Identität ist vorhanden,
- Source-Audit und Count-Gate sind dokumentiert.

Es bedeutet ausdrücklich **nicht**:
- ISIN vollständig,
- exakter MIC vollständig,
- Yahoo-Symbol vollständig,
- Kursdaten vollständig,
- Scalable-Handelbarkeit geprüft,
- U3K-Liquiditätsselektion abgeschlossen,
- P0 aktiviert,
- Kaufentscheidung.

Neue Rows dürfen deshalb zunächst `ACTIVE_SOURCE_CAPTURED` und `UNMAPPED` sein.

## 4. One-shot Remediation

Nach dem vollständigen Source-Superset folgt **ein gemeinsamer** Audit über alle
Segmente. Dieser Audit soll in einem Durchgang behandeln:

- fehlende/unklare Primärticker,
- exakte Primärbörse/MIC,
- RIC-/Provider-artige Ticker,
- Share Classes,
- ISIN/Identitäts-Deduplizierung,
- Yahoo-Mapping,
- Sonderfälle wie der legitime Ticker `NA`,
- Download-Fails,
- Quarantäne-/Corporate-Action-Anomalien.

Damit werden keine großen segmentweisen Mapping-Patches mehr vorgezogen.

## 5. Bestehende Schutzregeln bleiben unverändert

- Welt-Swing v7.2 bleibt produktive Trading-Autorität.
- Welt-Swing Long DEV bleibt nicht produktiv.
- P0 bleibt bis zur gesonderten Promotion aus.
- Alpha Vantage bleibt vollständig ausgeschlossen.
- Kein bezahlter Datenprovider wird vorausgesetzt.
- Der G3-Freeze `PASS_WITH_DOCUMENTED_QUARANTINE` bleibt unverändert bestehen.
- Die Zahl 3.000 ist weiterhin Ziel/Obergrenze des späteren U3K, nicht der Nenner
  des Source-Supersets.

## 6. Aktueller nächster Gate

`SOURCE_SUPERSET_14_SEGMENTS_COMPLETE`

Erst nach diesem Gate beginnt:
`FULL_IDENTITY_AND_PROVIDER_MAPPING_AUDIT`
