# Welt-Swing Long DEV — P0 Relative-Strength Augmentation v0.20

## Ausgangspunkt

v0.19 ist erfolgreich abgeschlossen:

- 2.037/2.037 augmentierte Feature-Zeilen
- Quarantäne 0
- Anglo American und Sasol zurückgewonnen
- kein P0-Lauf
- keine P0-Survivors
- keine numerischen P0-Pass-Schwellen
- Home-Market-RS und Sector-RS noch nicht implementiert

Der v0.19-As-of-Audit zeigt:
- 2.036 Werte mit AsOf 2026-08-21
- 1 Wert mit AsOf 2026-08-20

Der abweichende Wert ist **Webster Bank (`WS:US:WBS`, Yahoo `WBS`)**.

v0.20 behandelt diesen Fall fail-closed. Es wird kein Grund für den fehlenden 21.08.-Bar geraten. Webster Bank bleibt im Featurebestand, erhält für den synchronisierten RS-Layer aber `RS_NOT_VERIFIED_ASOF_MISMATCH`.

## Master-Basis

Der DEV-v0.1-Master verlangt:
- 20-/60-Tage-Renditedifferenz zum Heimatmarkt;
- soweit valide, zusätzlich zum Sektor;
- frühe Discovery darf reproduzierbare interne Peer-/Marktgruppen verwenden;
- bei nicht belastbarer Benchmarkgruppe `RS_NOT_VERIFIED`;
- Relative Stärke ist kein Trigger;
- Lane 4 verlangt positive 20-/60-Tage-Relative-Stärke plus konstruktive absolute Struktur und darf nicht allein aus RS bestehen;
- wo keine validierte quantitative Schwelle existiert, darf keine scheinpräzise Schwelle erfunden werden.

## v0.20 Home-Market-RS

v0.20 verwendet **keinen offiziellen Indexkurs** und behauptet das auch nicht.

Für die frühe RESEARCH_PARTIAL-Discovery wird pro `Primary_Universe_Index` ein reproduzierbarer interner Marktgruppen-Referenzwert berechnet:

`RS20 = Security_R20 - Leave-One-Out-Median_R20_der_synchronisierten_Primary-Universe-Peers`

analog für 60 Tage.

Der jeweilige Titel wird aus seiner eigenen Referenzmedian-Berechnung entfernt. Dadurch beeinflusst er die Vergleichsbasis nicht selbst.

Die tatsächlich im RESEARCH_PARTIAL enthaltenen Gruppen sind:
- AU_ASX200
- BR_IBRX100
- CN_CSI300
- IN_NIFTY50
- JP_N225
- TW_TW50
- US_SP1500
- ZA_TOP40

Nicht enthaltene oder instrumentseitig blockierte Segmente werden nicht künstlich rekonstruiert.

## As-of-Regel

Referenz-AsOf: **2026-08-21**.

Nur exakt auf diesen abgeschlossenen Bar synchronisierte Werte erhalten den internen Home-Market-RS.

Webster Bank mit AsOf 2026-08-20 erhält:
`RS_NOT_VERIFIED_ASOF_MISMATCH`.

Es erfolgt in v0.20 kein neuer Download und kein Sonder-Fallback.

## Sector RS

Der eingefrorene v0.19-Datensatz enthält keine auditierbare Sector-Klassifikation.

Deshalb gilt für alle Werte:
`RS_NOT_VERIFIED_NO_SECTOR_METADATA`.

Es wird keine Sektorzuordnung aus Namen, Branchenwissen oder Internetrecherche geraten.

## Lane-Parameter-Validierung

v0.20 führt eine **partielle semantische Validierung** durch.

Der Masterbegriff „positive 20-/60-Tage-Relative-Stärke“ wird für den Home-Market-RS-Komponentencheck deterministisch als:

`HomeMarket_RS20 > 0 AND HomeMarket_RS60 > 0`

abgebildet.

Das ist **nur ein Lane-4-Komponentenmerkmal** und niemals ein Lane-PASS oder Entry-Trigger.

Alle sonstigen v0.19-Featureverteilungen werden lediglich als P05/P25/Median/P75/P95-Evidenz ausgegeben. Keine Quantile werden in einen P0-Pass-Grenzwert umgewandelt.

`p0_numeric_pass_thresholds` bleibt leer.

## Governance

- keine externen Requests
- keine neuen Kursdownloads
- keine FX-/News-/Fundamentaldaten
- keine per-Security-Webcalls
- Alpha Vantage verboten
- kein `SWING_U3K_FROZEN`
- kein Full-Scan-Claim
- kein P0-PASS/FAIL
- keine P0-Survivors
- keine produktive Trade Authority
- v0.19-Artefakte bleiben unverändert

## Output

`output_p0_relative_strength_v0_20/`

- `p0_rs_augmented_v0.20.csv`
- `p0_rs_asof_audit_v0.20.csv`
- `home_market_cohort_rs_reference_v0.20.csv`
- `sector_rs_status_v0.20.csv`
- `lane_parameter_evidence_v0.20.csv`
- `p0_lane_parameter_registry_v0.20.json`
- `summary_v0.20.json`
- `stage_checkpoint_v0.20.json`
- `rs_manifest_v0.20.json`

## Nächster Schritt

`P0_LANE_PARAMETER_SHADOW_VALIDATION_AND_SECTOR_RS_PREP`

Dabei können die Lane-Regeln gegen historische/Shadow-Evidenz geprüft werden. Sector RS benötigt vorher eine auditierbare, eingefrorene Sektormetadatenquelle oder bleibt `RS_NOT_VERIFIED`.
