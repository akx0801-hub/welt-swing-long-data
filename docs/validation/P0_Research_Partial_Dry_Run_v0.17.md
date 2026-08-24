# Welt-Swing Long DEV — P0 RESEARCH_PARTIAL Parameter Freeze & Dry Run v0.17

## Zweck

v0.17 folgt auf den erfolgreich eingefrorenen `RESEARCH_PARTIAL`-Snapshot v0.16. Es führt **noch keinen validierten P0-Screen** aus. Es friert den aktuellen P0-Parameter-/Capability-Stand ein und prüft, ob alle 2.037 verifizierten Titel mit den persistenten lokalen Features verbunden werden können.

## Master-Regeln

P0 darf nur Daily OHLCV, lokale Features, Benchmark-/RS-Daten und statische Universe-Daten verwenden. Keine aktienweise Webrecherche.

Die sechs Price-First-Lanes bleiben Breakout/Compression/VCP, Pullback/Retest, Reclaim, Quiet Strength/Relative Strength, Post-Event Drift und Controlled Mean Reversion.

Die Master-Spezifikation verbietet scheinpräzise erfundene Schwellen. Ohne validierten quantitativen P0-Parametersatz darf keine vollständig validierte automatisierte P0-Ausführung behauptet werden.

## Inputs

- v0.16 RESEARCH_PARTIAL: **2.037** Zeilen
- kein `SWING_U3K_FROZEN`
- `output_full_3663/features_latest.csv`
- persistierte Full-Price-Features: 3.578 Zeilen
- Quelle: YFINANCE_FREE
- bisheriger P0-Status: `NOT_RUN_PARAMETERS_NOT_YET_PROMOTED`

## Bereits lokal verfügbar

EMA20, EMA50, SMA200, ATR14, R5/R20/R60, 20/60/252d-Hochs, 20/60d-Tiefs, EMA-/High-Distanzen, Range20 sowie 20d-Median-Volumen und -Turnover.

## Noch nicht ausreichend für automatisierten P0

- validierte algorithmische Lane-Schwellen
- Base/Pivot/VCP-Detektor
- mehrtägige Pullback/Retest/Reclaim/Higher-Low-Sequenzen
- aktuelles RVOL
- validierter Klimax-Detektor
- 20/60d-RS gegen Heimatmarkt und Sektor
- Impuls/Hold/Drift-Sequenzen
- Mean-Reversion-Stabilisierungsdetektor
- global synchronisierter aktueller As-of für einen echten aktuellen Scan

Die 18%-/20d- und 30%-/60d-Werte werden nur als Warnbeobachtungen geführt. Ungefähr 1 ATR, RVOL 1,3 und >2 ATR gehören zu späteren Bestätigungsregeln und werden nicht als P0-Pass-Schwellen verwendet.

## Governance

`p0_run=false`, `p0_dry_run=true`, `validated_automated_p0_run=false`, keine Survivors, kein Full-Scan-Claim, keine produktive Authority, Alpha Vantage verboten, keine externen Requests.

## Nächster Schritt

`P0_FEATURE_AUGMENTATION_AND_PARAMETER_VALIDATION`
