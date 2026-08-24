# P0 Research-Partial Integrity Fix v0.18

**Status:** DEV / RESEARCH / SHADOW ONLY  
**Scope:** technische Integritätskorrektur zwischen v0.17 und der nächsten P0-Feature-/Parameterstufe  
**Produktive Trading-Authority:** nein; `Welt-Swing v7.2` bleibt unverändert produktiv  
**Master-Spec:** `WELT-SWING LONG DEV v0.1` bleibt unverändert

## Anlass

v0.17 erzeugte einen linken Merge der 2.037 eingefrorenen RESEARCH_PARTIAL-Zeilen mit `features_latest.csv`. Zwei Punkte der damaligen Logik waren für eine revisionsfeste Match-/Usability-Aussage nicht ausreichend:

1. `feature_matched_rows` wurde als Länge des Left-Join-Ergebnisses ausgegeben. Diese Zahl ist bei einem Left Join immer 2.037 und belegt daher keinen tatsächlichen Feature-Match.
2. Die Prüfung `AsOf.astype(str).str.strip().eq('')` ist nach einem Left Join nicht fail-closed: ein durch einen fehlenden Join erzeugtes `NaN` wird zu der Zeichenfolge `"nan"` und gilt damit fälschlich als nicht leer.

Unabhängig davon hatte v0.17 bereits **2 P0-Datenfehler** und nur **2.035 vollständig vorhandene Core-Feature-Sätze** ausgewiesen. v0.18 verändert diese historischen Artefakte nicht, sondern korrigiert die technische Integritäts- und Readiness-Bewertung separat.

## v0.18-Regeln

v0.18 ermittelt tatsächliche Feature-Matches ausschließlich über den Pandas-Merge-Indikator. `AsOf` wird fail-closed geprüft: echte Missing Values, Leerstrings, die Sentinelwerte `nan`, `nat`, `none`, `null`, `na`, `n/a` sowie nicht parsebare Datumswerte sind ungültig.

Ein Datensatz ist für den nächsten P0-Entwicklungsschritt nur dann `PersistentFeatureUsable_v0_18=True`, wenn gleichzeitig gilt:

- tatsächlicher Feature-Row-Match,
- valides `AsOf`,
- vollständiger persistenter Core-Feature-Vektor gemäß der bereits in v0.17 verwendeten numerischen Felder.

Alle übrigen Datensätze werden fail-closed quarantänisiert. Erwarteter Sicherungsstand aus v0.17: **2.037 geprüft, 2.035 usable, 2 Quarantänefälle, 0 P0-Survivors**.

## Quarantänegründe

Zulässige Gründe sind ausschließlich:

- `UNMATCHED_FEATURE_ROW`
- `ASOF_MISSING`
- `ASOF_SENTINEL`
- `ASOF_INVALID_DATETIME`
- `CORE_FEATURE_INCOMPLETE`

Die Quarantäne-Datei weist die konkreten `WS_ID` und die tatsächlich vorhandenen Identitäts-/Status-/Reason-/Source-/Cache-/Coverage-Diagnosefelder aus. Es werden keine nicht vorhandenen Upstream-Diagnosen erfunden.

## Unveränderte Governance-Gates

- `p0_run=false`
- keine P0-Qualifikationsautomatik
- `p0_survivor_rows=0`
- `decisions_changed=0`
- `strict_u3k_frozen=false`
- kein Full-Scan-Claim
- keine produktive Trading-Authority
- `alpha_vantage_allowed=false`
- keine Preis- oder FX-Downloads
- keine Web-Calls je Security
- keine externen Referenzrequests
- keine Mutation des Canonical Masters
- keine nachträgliche Mutation der v0.17-Artefakte

## Inputs und Revisionsschutz

Der GitHub-Actions-Workflow pinnt die bereits verwendeten v0.16-/Price-Cache-Dateien sowie `summary_v0.17.json` und `p0_dry_run_observations_v0.17.csv` per Git-Blob-SHA. Zusätzlich prüft das Skript die in v0.17 bereits eingefrorenen SHA-256-Werte für Partial-Universe und `features_latest.csv`.

Der Offline-Selbsttest enthält explizit den v0.17-Regressionsfall eines fehlenden Left-Join-Matches, der ein echtes `NaN` in `AsOf` erzeugt, sowie Missing-/Sentinel-/Invalid-Date-/Core-Incomplete-Fälle.

## Outputs

`output_p0_research_partial_v0_18/` enthält:

- `summary_v0.18.json`
- `stage_checkpoint_v0.18.json`
- `integrity_fix_manifest_v0.18.json`
- `integrity_counts_v0.18.csv`
- `p0_integrity_observations_v0.18.csv`
- `p0_feature_quarantine_v0.18.csv`
- `p0_integrity_reason_counts_v0.18.csv`

## Nächster Schritt

Erst nach erfolgreichem v0.18-Gate folgt `P0_FEATURE_AUGMENTATION_AND_PARAMETER_VALIDATION`. v0.18 selbst qualifiziert keine Titel und aktiviert keine automatisierte P0-Selektion.
