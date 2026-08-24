# Welt-Swing Long DEV — RESEARCH_PARTIAL Snapshot v0.16

## Anlass

v0.15 hat bestätigt, dass beide getesteten S&P/TSX-Pfade im GitHub-Runner mit HTTP 403 blockiert sind. Kanada bleibt daher unverändert `NOT_VERIFIED`.

Die Instrument-Auflösung ist damit aktuell durch externe Quellenzugänge begrenzt. Weitere blinde Wiederholungen derselben blockierten Quelle wären nicht sinnvoll.

## Warum jetzt RESEARCH_PARTIAL?

Die autoritative Master-Spezifikation `WELT-SWING LONG DEV v0.1` erlaubt ausdrücklich `RESEARCH_PARTIAL`, wenn kein gültiges vollständiges Strict Universe verfügbar ist.

Pflicht sind dabei:
- dokumentierter Snapshot,
- enthaltene und fehlende Segmente,
- Counts,
- Coverage,
- As-of,
- keine Darstellung als vollständiger Welt-Scan.

v0.16 friert deshalb **nicht** `SWING_U3K_FROZEN` ein. Es friert ausschließlich einen auditierten `RESEARCH_PARTIAL`-Snapshot der bereits strikt verifizierten Teilmenge ein.

## Eingefrorener Ausgangszustand

- Full Eligibility rows: **3.657**
- aktuell verifizierte Strict Candidates: **2.037**
- weiterhin instrumentseitig unresolved: **650**
- übrige Non-Strict-Rows: **970**
- P0: **nicht gelaufen**

Fehlende Instrument-Segmente:
- EU_STOXX600: 365
- CA_TSX: 105
- KR_KOSPI200: 92
- HK_HSI: 82
- MX_IPC: 6

## v0.16-Output

`output_research_partial_v0_16/`

- `research_partial_universe_v0.16.csv`
- `missing_instrument_coverage_v0.16.csv`
- `coverage_by_segment_v0.16.csv`
- `missing_segments_v0.16.csv`
- `snapshot_manifest_v0.16.json`
- `stage_checkpoint_v0.16.json`
- `summary_v0.16.json`

## Governance

- kein `SWING_U3K_FROZEN`
- kein Full-Scan-Claim
- kein P0 in v0.16
- keine produktive Trade Authority
- Alpha Vantage bleibt verboten
- unresolved Securities bleiben ausgeschlossen und `NOT_VERIFIED`
- keine Hochrechnung fehlender Trefferzahlen

Zulässige spätere Schlussformulierung:
> bester verifizierter Kandidat innerhalb der tatsächlich geprüften Coverage

Nicht zulässig:
> weltweit bester Kandidat

## Nächster Schritt

Nach erfolgreichem v0.16-Snapshot folgt eine separat versionierte **P0-Parameter-Freeze-/Dry-Run-Stufe für RESEARCH_PARTIAL**. Erst dort wird geprüft, ob die vorhandenen Price-/Feature-Daten die im Master spezifizierten P0-Lanes vollständig und deterministisch tragen.


## Fix 1 — Count-Korrektur nach erstem GitHub-Run

Der erste v0.16-Run passierte die Frozen-Input-Gates und scheiterte anschließend korrekt an:

`Full eligibility rows 3657 != expected 3663`

Ursache: **3.663** ist die Größe des vorgelagerten Roh-/Price-Universe. Die von v0.16 tatsächlich konsumierte, eingefrorene Instrument-/Eligibility-Tabelle enthält **3.657** Zeilen.

Für den RESEARCH_PARTIAL-Snapshot gilt daher:

- Full Eligibility: **3.657**
- Included Verified Strict: **2.037**
- Instrument Unresolved: **650**
- Other Non-Strict: **970**
- Verified Strict Coverage: **55,7014 %**
- Instrument-Unresolved-Anteil: **17,7741 %**

Die Frozen-Input-Hashes und fachlichen Regeln bleiben unverändert. Dies ist ein reiner Count-/Validation-Bugfix innerhalb v0.16.
