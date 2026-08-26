# Welt-Swing Long DEV — P0 Lane Parameter Shadow Validation & Sector-RS Prep v0.21

## Ausgangspunkt

v0.20 ist erfolgreich abgeschlossen und bleibt unverändert.

Aktueller v0.20-Evidenzstand:
- 2.037 Input-Zeilen
- 2.036 synchronisierte Home-Market-RS-Zeilen
- 1 As-of-Ausnahme: Webster Bank (`WS:US:WBS`), AsOf 2026-08-20 statt 2026-08-21
- 706 Werte mit positivem 20d- und 60d-Home-Market-RS-Komponentenmerkmal
- Sector RS: 0
- keine P0-Entscheidungen
- keine Survivors
- keine numerischen P0-Pass-Schwellen
- Alpha Vantage: verboten

## Zweck von v0.21

v0.21 ist keine P0-Auswahlstufe. Die Stufe hat zwei Aufgaben:

1. vorhandene Lane-Merkmale als **Shadow-Komponenten** sichtbar und auditierbar machen, ohne daraus PASS/FAIL oder Survivor-Status zu erzeugen;
2. den fehlenden Sector-RS-Layer technisch und governance-seitig vorbereiten.

## Review-Korrekturen vor Ausführung

Die vorbereitete v0.21-Fassung wurde vor dem Lauf gegen den DEV-Master geprüft und ausschließlich vorwärts gehärtet; v0.20 bleibt unverändert.

- Shadow-Komponenten besitzen zusätzlich einen expliziten Status `VERIFIED_TRUE`, `VERIFIED_FALSE`, `NOT_VERIFIED_ASOF_MISMATCH` oder `NOT_VERIFIED_MISSING_INPUT`. Dadurch werden ein echtes negatives Merkmal und eine Datenlücke nicht mehr zusammengezählt.
- Die bekannte Webster-Bank-As-of-Ausnahme wird fail-closed auf **alle dynamischen Shadow-Komponenten** angewendet, nicht nur auf Home-Market-RS.
- Der Stage-Checkpoint enthält die im DEV-Master geforderten Auditfelder: Start, Ende, Input Hash, Parameter Hash, Output Hash, Data Error Count, Quarantine Count und Failed Source zusätzlich zu Counts, Status und Next Stage.
- Das Manifest prüft die erzeugten Evidence-Artefakte per SHA-256; keine historische v0.20-Datei wird verändert.

Diese Korrekturen ändern keine Tradingregel und erzeugen keine P0-Schwelle.

## Shadow-Komponenten

Es werden nur mathematisch eindeutige Relationen oder Vorzeichen als Beobachtungen abgeleitet:

- Close > EMA20 / EMA50 / SMA200
- EMA20-/EMA50-Slope > 0
- R20 / R60 > 0
- 5-Tage-Range kleiner als 20-Tage-Range
- 5-Tage-True-Range-Mittel kleiner als 20-Tage-Mittel
- RecentLow10 > PriorLow10
- Post-Impulse-Minimum hält den Impulse-Close
- Post-Impulse-Latest liegt über dem Impulse-Close
- Home-Market-RS20 > 0
- Home-Market-RS60 > 0
- Home-Market-RS20 und RS60 beide > 0

Diese Relationen sind **keine** P0-Pass-Schwellen. Empirische Quantile oder scheinpräzise Grenzwerte werden nicht als Regeln übernommen.

## Lane-Status

Alle sechs Lanes bleiben `NOT_ALLOWED` für automatisierte P0-Entscheidungen.

v0.21 korrigiert lediglich vorwärts die veraltete Lane-4-Metadatenformulierung aus v0.20: Home-Market-RS ist für 2.036 synchronisierte Werte vorhanden und wird deshalb nicht länger als „missing“ bezeichnet.

Für Lane 4 bleiben insbesondere offen:
- Sector RS
- validierte Definition eines vertikalen Momentum-Exzesses
- validierte Kopplung der RS-Komponente an Breakout/Pullback/Retest/Reclaim/Drift

## Sector-RS Prep

Der eingefrorene v0.20-Input wird auf rohe, auditierbare Sektormetadaten geprüft. Generated-Felder wie `Sector_RS_Status_v0_20` zählen ausdrücklich nicht als Taxonomie.

Wenn keine rohe Taxonomie vorhanden ist:
`RS_NOT_VERIFIED_NO_FROZEN_SECTOR_METADATA`.

Der Datenvertrag für einen späteren Bulk-Sector-Layer verlangt mindestens:
- WS_ID
- Sector_Taxonomy
- Sector_Code
- Sector_Name
- Source_Name
- Source_Reference
- Source_Version_or_AsOf
- Mapping_Status

Verboten:
- per-Security-Web-Fanout
- Namensraten
- stilles Mischen verschiedener Taxonomien ohne Crosswalk
- unversionierte Sektorlabels
- Alpha Vantage

## Governance

- keine externen Requests
- keine neuen Kursdownloads
- keine FX-/News-/Fundamentaldaten
- kein P0 PASS/FAIL
- keine P0-Survivors
- kein `SWING_U3K_FROZEN`
- kein Full-Scan-Claim
- keine produktive Trade Authority
- keine Änderung des DEV-v0.1-Masters oder historischer v0.20-Artefakte

## Output

`output_p0_lane_shadow_validation_v0_21/`

- `p0_shadow_component_observations_v0.21.csv`
- `p0_shadow_component_counts_v0.21.csv`
- `p0_lane_shadow_validation_matrix_v0.21.csv`
- `sector_metadata_inventory_v0.21.csv`
- `sector_metadata_contract_v0.21.json`
- `p0_lane_parameter_registry_v0.21.json`
- `summary_v0.21.json`
- `stage_checkpoint_v0.21.json`
- `shadow_manifest_v0.21.json`

## Nächster Schritt

`P0_SECTOR_METADATA_BULK_SOURCE_PROBE_AND_SHADOW_RULE_TEST_DESIGN`

Erst dort wird geprüft, ob eine reproduzierbare Bulk-Sektorquelle die notwendige Taxonomie liefern kann. Ohne eine solche Quelle bleibt Sector RS `RS_NOT_VERIFIED`.
