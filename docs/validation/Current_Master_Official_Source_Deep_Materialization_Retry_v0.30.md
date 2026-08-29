# WELT-SWING LONG DEV — Official Source Deep Materialization Retry v0.30

**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Stage:** `CURRENT_MASTER_OFFICIAL_SOURCE_DEEP_MATERIALIZATION_RETRY`

## Ausgangslage

v0.29 lief technisch vollständig erfolgreich, materialisierte aber noch kein fehlendes Segment als reproduzierbare Membership-Evidence.

Die Ursachen waren nun klar:

- S&P-DJI-Routen: GitHub Runner erhielt HTTP 403.
- JSE-Routen: GitHub Runner erhielt HTTP 403.
- NZX: öffentliche Constituents-Anzeige ausdrücklich eingestellt / Subscription-Verweis.
- B3: HTML lieferte nur die Angular-App-Shell; die Portfolio-Tabelle wird dynamisch geladen.
- KRX: die bisherige URL lieferte nur einen JavaScript-Redirect.
- BMV: die offizielle Special-Information-Seite lieferte zahlreiche aktuelle und historische Dokumentlinks.

v0.30 wiederholt deshalb **nicht** dieselben zehn Probes, sondern vertieft nur drei konkrete offizielle Workstreams.

## 1. B3 / IBrX 100

Die offizielle B3-Anwendung lädt die aktuelle Indexzusammensetzung über:

`indexProxy/indexCall/GetPortfolioDay/<base64-json>`

v0.30 ruft genau diesen offiziellen B3-Endpunkt für `IBXX` mit PageSize 200 auf.

Das Base64-Payload enthält ausschließlich:

- language = pt-br
- pageNumber = 1
- pageSize = 200
- index = IBXX
- segment = 1

Erwartete Felder aus der offiziellen Antwort:

- `cod`
- `asset`
- `type`
- `theoricalQty`
- `part`

Ab mindestens 80 eindeutigen Security Codes wird der Status:

`MATERIALIZED_OFFICIAL_B3_CURRENT_MEMBERSHIP_EVIDENCE`

gesetzt.

Auch dann gilt noch:

`Canonical_Import_v0_30 = false`

Identity-/MIC-/Security-Type-Reconciliation erfolgt erst im Folgestage.

## 2. KRX / KOSPI 200

v0.30 prüft einmalig den offiziellen KRX-internen Datenendpunkt:

`/comm/bldAttendant/getJsonData.cmd`

mit BLD:

`dbms/MDC/STAT/standard/MDCSTAT00701`

und KOSPI-200-Code:

- indIdx = 1
- indIdx2 = 028
- requested trade date = 20260828

Es wird **kein Login** durchgeführt und es werden keine Zugangsdaten verwendet.

Wenn KRX den anonymen Request mit Login-/Session-Block beantwortet, wird dies explizit als:

`KRX_OFFICIAL_INTERNAL_API_AUTH_OR_SESSION_BLOCKED`

klassifiziert.

Nur eine echte offizielle Constituents-Antwort mit mindestens 180 eindeutigen Codes darf als Membership-Evidence gelten.

## 3. BMV / S&P-BMV IPC

Aus dem eingefrorenen v0.29-Kandidatenregister wird ausschließlich das aktuelle offizielle Dokument:

`SP BMV IPC Rebalance Announcement (English) - Final.pdf`

ausgewählt, bevorzugt aus der BMV-`CTEN_INCM`-Route.

v0.30:

1. lädt genau dieses offizielle PDF,
2. speichert es unverändert,
3. extrahiert den PDF-Text mit `pypdf`,
4. kennzeichnet das Dokument als materialisiert, falls die Semantik eindeutig S&P/BMV IPC + Final bestätigt.

Das PDF allein führt noch **nicht** zu einem Canonical Import. Eine belastbare vollständige Membership-Extraktion und Identity-Reconciliation bleibt ein eigener Schritt.

## 4. Nicht erneut abgefragte Blocker

v0.30 wiederholt keine bekannten nutzlosen Requests:

- US_SP1500: `SOURCE_BLOCKED_FULL_EXPORT_LOGIN_REQUIRED`
- AU_ASX200: GitHub-Runner 403 + kein vollständiger Export
- NZ_NZX50: öffentlicher Constituents-Zugang eingestellt / Subscription
- ZA_TOP40: GitHub-Runner 403; direkter offizieller Asset-Pfad erforderlich

## 5. Governance

v0.30 darf nicht:

- den 1.535er Current Master verändern,
- neue kanonische Segmente importieren,
- Instrumententscheidungen ändern,
- Eligibility-Promotions durchführen,
- Preise laden,
- Sector RS berechnen,
- P0 starten,
- Alpha Vantage verwenden,
- produktive Trading-Autorität erzeugen.

Maximal drei externe Requests, keine Per-Security-Webcalls.

## 6. Outputs

- `b3_ibrx100_official_raw_v0.30.json` (wenn Endpoint erreichbar)
- `b3_ibrx100_membership_v0.30.csv`
- `krx_kospi200_official_raw_v0.30.txt`
- `krx_kospi200_membership_v0.30.csv`
- `bmv_ipc_final_rebalance_v0.30.pdf` (wenn abrufbar)
- `bmv_ipc_final_rebalance_text_v0.30.txt`
- `source_deep_materialization_status_v0.30.csv`
- `summary_v0.30.json`
- `stage_checkpoint_v0.30.json`
- `manifest_v0.30.json`
- `WELT-SWING-CURRENT-Handoff-v0.30.md`
- `WELT-SWING-CURRENT-Handoff-CURRENT.md`

## 7. Nächster Stage

Wenn mindestens B3 oder KRX echte offizielle Membership-Evidence materialisiert:

`CURRENT_MASTER_MATERIALIZED_OFFICIAL_MEMBERSHIP_IDENTITY_RECONCILIATION`

Wenn beide weiterhin blockiert bleiben:

`CURRENT_MASTER_OFFICIAL_SOURCE_ACCESS_REMEDIATION_V0_31`

Damit wird der nächste Schritt vom tatsächlichen Ergebnis bestimmt und nicht vorweggenommen.
