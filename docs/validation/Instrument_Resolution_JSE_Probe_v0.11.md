# Welt-Swing Long DEV — JSE ISIN Bulk Probe v0.11

## Zweck

v0.11 ist eine **Evidence-only-Stufe** für die 17 verbleibenden `ZA_TOP40`-Zeilen.

Sie klassifiziert **keine** Aktie. Ziel ist nur zu prüfen, ob der offizielle JSE-Downloadpfad für die aktuelle Equities-ISIN-Gesamtdatei reproduzierbar materialisiert werden kann.

## Frozen Ausgangszustand

v0.10 ist abgeschlossen mit KRX Source Block:

- Manual Review: **667**
- Strict Candidates: **2.020**
- KR_KOSPI200 unresolved: **92**
- KRX HTTP: **400**
- Strict Freeze: **false**
- P0: **false**

## Offizielle JSE-Quelle

`https://clientportal.jse.co.za/downloadable-files?RequestNode=%2FISIN%2FEquities`

Dort wird aktuell `isinfull_e.zip` für Equities ausgewiesen.

## Request-Governance

Maximal **2** externe Requests:

1. JSE Equities-ISIN-Folder
2. daraus deterministisch entdeckte `isinfull_e.zip`

Keine per-Security-Abfragen.

## Was v0.11 speichert

- HTTP-/Hash-/Content-Metadaten
- entdeckte ZIP-URL
- ZIP-Archivmitglieder
- begrenzte Text-Samples aus lesbaren Archivdateien
- die 17 eingefrorenen ZA-Targets
- unveränderte 667er Review Queue
- Summary und Source Status

## Keine Klassifikation in v0.11

Auch bei erfolgreichem ZIP:

- keine PASS/FAIL-Entscheidung,
- keine Namensheuristik,
- keine Formatannahme,
- keine Veränderung der 2.020 Strict Candidates.

Erst wenn Dateifelder und JSE-Semantik eindeutig dokumentiert sind, darf v0.12 klassifizieren.

## Governance

- Alpha Vantage verboten
- keine Preisdownloads
- keine FX-Downloads
- keine per-Security-Webcalls
- P0 aus
- keine produktive Trade Authority
- Canonical Master unverändert
