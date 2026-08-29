# WELT-SWING LONG DEV — Missing-Segment Official Source Materialization v0.29

**Status:** DEV / RESEARCH / SHADOW — NOT PRODUCTIVE  
**Stage:** `CURRENT_MASTER_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION`

## Zweck

v0.28 hat die Current-Master/Clean-Restart-Lineage als primären Universe-Strang festgeschrieben: 1.535 Securities aus 7 von 14 Zielsegmenten. v0.29 untersucht ausschließlich die sieben noch fehlenden Segmente und materialisiert nur offizielle Source-Evidence.

Fehlend:

- US_SP1500
- MX_IPC
- KR_KOSPI200
- AU_ASX200
- NZ_NZX50
- BR_IBRX100
- ZA_TOP40

Die alte Phase2-/3663-Lineage bleibt Engineering-/Diagnostik-Evidence und darf keine fehlenden Memberships in den Current Master liefern.

## Offizielle Quellenlage vor dem Stage

Die vor Erstellung dieses Stages aktuelle Verifikation ergab:

- S&P DJI führt offizielle Produktseiten für S&P Composite 1500, S&P/BMV IPC, S&P/ASX 200 und S&P/NZX 50. Sichtbare „Full Constituents List“-UI wird nicht mit einem frei reproduzierbaren vollständigen Export gleichgesetzt.
- BMV stellt eine offizielle „Special Information“-Route mit „CONSTITUENTS LIST“ und Index-Dokumenten bereit.
- KRX Data Marketplace ist die offizielle KOSPI-200-Datenroute; frühere DEV-Probes haben technische/sessionbezogene Error-Landing-Pages gezeigt, daher weiterhin fail-closed.
- NZX erklärt aktuell ausdrücklich, dass Index-Constituent-Daten nicht mehr auf NZX.com angezeigt werden und verweist für weitere Informationen/Subscription an S&P DJI.
- B3 stellt für den IBrX 100 eine offizielle „Carteira do Dia / Carteira Teórica“-Seite bereit.
- JSE stellt die FTSE/JSE Africa Index Series und aktuelle Review-/Index-Dokumente offiziell bereit.

## Netzwerk-Governance

v0.29 ist kein Crawler.

Es gibt exakt zehn vorkonfigurierte GET-Requests auf offizielle Domains. Gefundene Links werden nur inventarisiert und nicht automatisch aufgerufen.

`candidate_link_follow_requests = 0`

`per_security_web_calls = false`

Erlaubt sind ausschließlich:

- spglobal.com
- bmv.com.mx
- krx.co.kr
- nzx.com
- b3.com.br
- jse.co.za

## Segmentbehandlung

### US_SP1500

Der bekannte Gate-Status bleibt:

`SOURCE_BLOCKED_FULL_EXPORT_LOGIN_REQUIRED`

Die S&P-DJI-Produktseite bestätigt den Index und die Constituents-UI; v0.29 darf daraus keinen vollständigen 1500er Export behaupten.

### MX_IPC

S&P DJI und BMV werden gemeinsam geprüft. Rebalance-/Change-Dokumente sind nicht automatisch die vollständige aktuelle 35er-Mitgliedschaft. Deshalb keine automatische Membership-Promotion.

### KR_KOSPI200

Die feste offizielle KRX-Route wird erneut geprüft. HTTP 200 auf einer Error-/503-Landing-Page gilt als Fehler.

### AU_ASX200

Die offizielle S&P-DJI-Produktseite wird gespeichert. Indexgröße oder Top-10-Anzeige genügt nicht als vollständiges Importfile.

### NZ_NZX50

Wenn die offizielle NZX-Seite weiterhin die öffentliche Constituents-Anzeige ausdrücklich verneint, wird fail-closed klassifiziert:

`SOURCE_BLOCKED_PUBLIC_CONSTITUENT_DATA_WITHDRAWN_OR_SUBSCRIPTION_REQUIRED`

### BR_IBRX100

Die offizielle B3-Tagesportfolio-Seite wird zusätzlich strukturiert geparst. Wenn mindestens 80 eindeutige Security Codes aus der sichtbaren theoretischen Portfolio-Tabelle materialisiert werden, lautet der Evidenzstatus:

`OFFICIAL_CURRENT_MEMBERSHIP_EVIDENCE_MATERIALIZED_IDENTITY_IMPORT_PENDING`

Das ist ausdrücklich noch kein Universe-Import. Identity, Primary MIC/Ticker, Security Type und Source-AsOf bleiben Aufgaben des Folgestages.

### ZA_TOP40

JSE Index-Series- und Dokumentseiten werden gespeichert. Review-/Appendix-Kandidaten werden inventarisiert, aber nicht automatisch gefolgt oder zu einem aktuellen Top-40-Satz zusammengesetzt.

## Keine Mutation

v0.29 verändert nicht:

- den 1.535er Current Master,
- Instrumententscheidungen,
- Eligibility,
- Preis-Cache,
- Sector RS,
- P0,
- produktive Trading-Autorität.

Alpha Vantage bleibt verboten.

## Outputs

- `official_source_probe_status_v0.29.csv`
- `official_candidate_links_v0.29.csv`
- `b3_ibrx100_materialized_membership_v0.29.csv`
- `missing_segment_materialization_status_v0.29.csv`
- `imported_segment_provenance_carryforward_v0.29.csv`
- `raw_official_source/*.html`
- `summary_v0.29.json`
- `stage_checkpoint_v0.29.json`
- `manifest_v0.29.json`

Zusätzlich:

- `WELT-SWING-CURRENT-Handoff-v0.29.md`
- `WELT-SWING-CURRENT-Handoff-CURRENT.md`

## Erwarteter Status

`PARTIAL` ist fachlich korrekt, solange nicht alle sieben fehlenden Segmente über vollständige, reproduzierbare offizielle Membership-Evidence verfügen.

## Nächster Stage

`CURRENT_MASTER_OFFICIAL_MEMBERSHIP_IDENTITY_IMPORT_AND_SOURCE_PROVENANCE_FREEZE`

Nur tatsächlich materialisierte offizielle Evidenz darf dorthin weitergereicht werden.
