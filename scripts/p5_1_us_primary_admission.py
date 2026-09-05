#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
OUT=ROOT/"output_p5_1_admission"
MD=ROOT/"docs"/"spec"/"P5_1_US_Primary_Admission_Readiness.md"
POLICY=[("COMMON_STOCK","ADMIT","XNYS/XNAS primary common, ISIN+MIC+ticker, not ADR/ETF."),("ORDINARY_SHARE","ADMIT","Same if US primary listing."),("PREFERRED","DISCOVER","Visible; never canonical scan default."),("ETF","EXCLUDE","Not single-name scan."),("FUND","EXCLUDE","Same as ETF."),("UNIT","EXCLUDE","Not standard scan."),("WARRANT","EXCLUDE","Not standard scan."),("RIGHT","EXCLUDE","Not standard scan."),("ADR","EXCLUDE","US listing of non-US issuer; not US Primary."),("ADS","EXCLUDE","Same as ADR."),("BDC","REVIEW","Fail-closed until extra policy."),("REIT","REVIEW","Fail-closed until extra policy."),("LP","REVIEW","Fail-closed until extra policy."),("MLP","REVIEW","Fail-closed until extra policy."),("SPAC","EXCLUDE","Not mature operating common."),("UNKNOWN","EXCLUDE","No mass-admit then classify later.")]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    if sum(1 for _ in open(FROZEN, encoding="utf-8"))!=1: raise SystemExit("frozen")
    uni_sha=sha(UNI)
    uni=list(csv.DictReader(open(UNI, encoding="utf-8-sig")))
    elig=list(csv.DictReader(open(ELIG, encoding="utf-8")))
    if len(uni)!=1633: raise SystemExit("uni")
    if sum(1 for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")!=759: raise SystemExit("strict")
    ident=[(r["WS_ID"], r["ISIN"], r["Primary_MIC"], r["Primary_Ticker"]) for r in uni]
    us_now=sum(1 for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"})
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT/"instrument_admission_policy.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=["Category","Decision","Rule"]); w.writeheader()
        for c,d,r in POLICY: w.writerow({"Category":c,"Decision":d,"Rule":r})
    md="""# P5.1 US Primary Segment Admission & Expansion Readiness

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
US Primary fachlich vorbereitet. Aktuell XNYS/XNAS Membership = %s. Nicht geladen.

## 17. Manager Gate
Naechster Auftrag nur explizit: US-1 Controlled Segment Build.
Nicht in US-1: 15 REVIEW, 686 UNKNOWN, Kanada TSX, 3663, 1296-Welle, Freeze.
P5.1 STOPP. Kein Datenbau.
"""%us_now
    MD.parent.mkdir(parents=True, exist_ok=True)
    MD.write_text(md, encoding="utf-8")
    if [(r["WS_ID"], r["ISIN"], r["Primary_MIC"], r["Primary_Ticker"]) for r in uni]!=ident or sha(UNI)!=uni_sha: raise SystemExit("universe mutated")
    summary={"stage":"P5_1_US_PRIMARY_ADMISSION","version":"v0.56-P5.1","run_mode":"READ_ONLY_ADMISSION","p5_1_status":"READY_FOR_SEPARATE_US_1_BUILD","ready_means":"architecture_only_not_data","first_us1_slice":"SP500_COMMON_XNYS_XNAS_NO_ADR_ETF_PREF","primary_mics":["XNYS","XNAS"],"identity_minimum":"ISIN+Primary_MIC+Primary_Ticker","isin_fallback":"NONE_FAIL_CLOSED","us_membership_now":us_now,"strict":759,"membership":1633,"universe_write":False,"eligibility_promoted":False,"u3k_frozen_members":0,"productive":False,"next_data_build":"NONE_WITHOUT_US1_MANAGER_ORDER","as_of_utc":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    json.dump(summary, open(OUT/"summary_p5_1.json","w",encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
