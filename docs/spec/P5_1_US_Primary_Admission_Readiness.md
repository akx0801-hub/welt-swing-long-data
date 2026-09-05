# P5.1 US Primary Segment Admission & Expansion Readiness

HEAD `4235f7e`. READ-ONLY. Strict=759. Frozen=0. Universe_Write=NO. Kein US-Download.

## 1. Executive Decision
P5.1 STATUS: READY FOR SEPARATE US-1 BUILD
READY = Architektur reicht fuer separaten US-1-Auftrag. NICHT: Daten geladen / gemappt / im Universe / eligible / U3K erweitert.
ERSTE SCHEIBE: S&P 500 Common auf XNYS/XNAS, ADR/ETF/Pref ausgeschlossen.

## 2. Definition US Primary
US Primary = primaeres Handelslisting eines Common/Ordinary auf XNYS oder XNAS.
US-Emittent != US-Primary-Listing. NYSE-ADR eines Nicht-US-Emittenten ist KEIN US Primary.
Zulaessig: XNYS, XNAS. Nicht in US-1: ARCX, BATS, IEX, OTC, Pink.

## 3-4. Membership / Instrument
Siehe instrument_admission_policy.csv.
Ordinary/Common: ADMIT wenn Primary + Identity + keine ADR-Kennung.
Preferred: DISCOVER, nie Canonical-Scan. ETF/Fund/Unit/Warrant/Right/SPAC/ADR: EXCLUDE.
REIT/BDC/LP/MLP: REVIEW fail-closed.

## 5. Multi-Share-Class
Discovery: Klassen getrennt, kein Merge. Canonical spaeter: eine Ordinary/Common je Emittent x MIC (hoehere MedianTurnover20_EUR, sonst Index-Mitglied). Pref nie Default.

## 6. Dual-Listing
Kein MIC-Merge. US-Zeile bleibt US-Zeile, auch wenn derselbe Emittent in 1633 unter XETR/XLON liegt.

## 7. Identity Minimum
ISIN + Primary MIC + Primary Ticker. Ohne ISIN = FAIL-CLOSED. CUSIP ersetzt ISIN nicht. Yahoo ist Mapping, nicht Identitaet.

## 8. Evidence
1 S&P 500 official constituents  2 NYSE/Nasdaq listing directory  3 ISIN/LEI registry  4 Closed-Map Share-Class analog v0.42.
Unzulaessig: Wikipedia, anonyme Listen, Broker-Screener, Scalable.

## 9. Mapping
Identity -> Evidence -> Provider Mapping. Probe, dann Apply nach Manager-Gate. Max 2 Retry, dann FAIL. Kein Mapping bei EXCLUDE/REVIEW oder unvollstaendiger Identity. P5.1 mappt nichts.

## 10-11. History / Liquidity (spaeter, nicht jetzt)
260 Unique / 252 Valid / 18/20 Sessions; keine Zukunft, keine Dubletten.
MedianTurnover20_EUR: >=20m PREFERRED, >=15m STANDARD, 5-15m EXCEPTION, <5m FAIL.
FX: USDEUR=X, Quote_Scale 1 fuer USD.

## 12-13. Canonical / Execution
Eine Scan-Klasse je Emittent x XNYS-oder-XNAS. Scalable getrennt, keine Live-Pruefung, keine Membership-Voraussetzung.

## 14. Gates fuer spaeteres US-1
0 Definition (dieses Dokument) 1 Source S&P500 2 Admission 3 Evidence 4 Mapping Probe/Apply 5 History 6 Liquidity 7 Eligibility Dry-Run Sidecar 8 Manager Gate vor Master-Write.
Kein Gate gibt das naechste frei.

## 15. Fail-Closed
Nicht raten. UNKNOWN bleibt UNKNOWN. Keine Massenaufnahme mit spaeterer Reparatur (Lehre 671/686).

## 16. Readiness
US Primary fachlich vorbereitet. Aktuell XNYS/XNAS Membership = 0. Nicht geladen.

## 17. Manager Gate
Naechster Auftrag nur explizit: US-1 Controlled Segment Build.
Nicht in US-1: 15 REVIEW, 686 UNKNOWN, Kanada TSX, 3663, 1296-Welle, Freeze.
P5.1 STOPP. Kein Datenbau.
