#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
OUT=ROOT/"output_us1_integration_gate"
US1=ROOT/"output_us1"
IVV="https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v2/get-product-data?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=us-ishares&locale=en_US&portfolioId=239726&userType=individual&component=holdings"
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rcsv(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def wcsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows: path.write_text("", encoding="utf-8"); return
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
def norm(t): return (t or "").replace(".","").replace("-","").upper()
def main():
    if sum(1 for _ in open(FROZEN,encoding="utf-8"))!=1: raise SystemExit("frozen")
    uni_sha=sha(UNI); uni=rcsv(UNI)
    if len(uni)!=1633: raise SystemExit("uni")
    ident=[(r["WS_ID"],r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in uni]
    if sum(1 for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"})!=0: raise SystemExit("us_in_1633")
    adm=rcsv(US1/"admission_admitted.csv"); rev=rcsv(US1/"admission_review.csv")
    elig=rcsv(US1/"eligibility_dry_run_us1.csv"); can=rcsv(US1/"canonical_scan_us1.csv")
    js=requests.get(IVV, timeout=45, headers={"User-Agent":"welt-swing-us1/0.1"}).json()
    dp=js["componentsByNameMap"]["holdings"]["containersByNameMap"]["all"]["dataPointsByNameMap"]
    ivv_asof=str(dp.get("asOfDate",{}).get("formattedValue") or "")
    tickers=dp["ticker"]["value"]; isins=dp["isin"]["value"]
    ac=dp.get("assetClass",{}).get("value") or [""]*len(tickers)
    ivv={}
    for t,i,a in zip(tickers,isins,ac):
        if a=="Equity": ivv[norm(t)]={"ticker":t,"isin":i,"asset":a}
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump({"source":"iShares_IVV","as_of":ivv_asof,"retrieved_utc":ASOF,"equity_n":len(ivv),"class":"INSTITUTIONAL_RANK4","url":IVV}, open(OUT/"ivv_source_snapshot.json","w",encoding="utf-8"), indent=2)
    elig_by={r["WS_ID"]:r for r in elig}
    can_ids={r["Canonical_WS_ID"] for r in can}
    rev_out=[]
    for r in rev:
        reasons=[]
        if "REIT" in r["Admission_Reason"]: reasons.append("REVIEW_REIT")
        if not r["ISIN"] or r["ISIN"]=="NOISIN": reasons.append("REVIEW_IDENTITY")
        if "|" in (r["ISIN"] or ""): reasons.append("REVIEW_SHARE_CLASS")
        if "|" in (r["Primary_MIC"] or "") or not r["Primary_MIC"] or r["Primary_MIC"]=="NOMIC": reasons.append("REVIEW_PRIMARY_MIC")
        cat="REVIEW_MULTIPLE_REASONS" if len(set(reasons))>1 else (reasons[0] if reasons else "REVIEW_OTHER")
        k=norm(r["Primary_Ticker"]); hit=ivv.get(k)
        rev_out.append({**{x:r[x] for x in ("WS_ID","Primary_Ticker","ISIN","Primary_MIC","Admission_Reason","GICS_Sector") if x in r},"Review_Category":cat,"IVV_Ticker": (hit or {}).get("ticker",""),"IVV_ISIN":(hit or {}).get("isin",""),"Ready":"NOT_READY","Integration_Class":"D"})
    wcsv(OUT/"review_104_classified.csv", rev_out)
    matrix=[]; a_rows=[]; cls=Counter()
    for r in adm:
        e=elig_by.get(r["WS_ID"], {})
        k=norm(r["Primary_Ticker"]); hit=ivv.get(k)
        memb="MEMBERSHIP_VERIFIED" if hit and r["ISIN"]==hit["isin"] else ("MEMBERSHIP_CONFLICT" if hit else "MEMBERSHIP_SECONDARY_ONLY")
        ident_ok=("|" not in r["ISIN"] and r["ISIN"].startswith("US") and r["Primary_MIC"] in {"XNYS","XNAS"} and r["Primary_Ticker"])
        hist=e.get("History_State",""); liq=e.get("Liquidity_Class",""); dry=e.get("Eligibility_DryRun","")
        hona=r["Yahoo_Symbol"]=="HONA"; ic="E"
        if r.get("Instrument_Type")=="REIT_REVIEW" or r["GICS_Sector"]=="Real Estate": ic="D"
        elif not ident_ok: ic="D"
        elif memb in {"MEMBERSHIP_CONFLICT","MEMBERSHIP_SECONDARY_ONLY"}: ic="B"
        elif hona or hist!="PASS" or dry=="HISTORY_FAILURE": ic="E"
        elif dry!="ELIGIBLE" or liq not in {"PREFERRED","STANDARD"}: ic="E"
        elif memb=="MEMBERSHIP_VERIFIED" and ident_ok and hist=="PASS" and dry=="ELIGIBLE" and r["WS_ID"] in can_ids: ic="A"
        else: ic="B"
        cls[ic]+=1
        matrix.append({"WS_ID":r["WS_ID"],"Ticker":r["Primary_Ticker"],"ISIN":r["ISIN"],"MIC":r["Primary_MIC"],"Instrument":r["Instrument_Type"],"Membership":memb,"IVV_ISIN":(hit or {}).get("isin",""),"Identity":"PASS" if ident_ok else "FAIL","History":hist,"Liquidity":liq,"Eligibility":dry,"Canonical":"PASS" if r["WS_ID"] in can_ids else "FAIL","Integration_Class":ic,"HONA":"YES" if hona else "NO"})
        if ic=="A":
            a_rows.append({"WS_ID":r["WS_ID"],"ISIN":r["ISIN"],"Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],"Yahoo_Symbol":r["Yahoo_Symbol"],"Issuer":r["Issuer"],"MedianTurnover20_EUR":e.get("MedianTurnover20_EUR",""),"Note":"CLASS_A_CANDIDATE_NOT_UNIVERSE"})
    wcsv(OUT/"evidence_matrix_399.csv", matrix)
    wcsv(OUT/"US1_INTEGRATION_CANDIDATES.csv", a_rows)
    json.dump({"ticker":"HONA","isin":"US43849R1059","bars":58,"ivv_hona":bool(ivv.get("HONA")),"ivv_hon":ivv.get("HON",{}),"class":"E","repairable":"NO","reason":"Short history; IVV lists HONA and HON as distinct. Not a mapping mix-up."}, open(OUT/"hona_analysis.json","w",encoding="utf-8"), indent=2)
    if [(x["WS_ID"],x["ISIN"],x["Primary_MIC"],x["Primary_Ticker"]) for x in rcsv(UNI)]!=ident: raise SystemExit("identity")
    if sha(UNI)!=uni_sha: raise SystemExit("universe mutated")
    status="READY_FOR_US1_INTEGRATION_WRITE_GATE" if len(a_rows)>=300 else "NOT_READY_EVIDENCE_ADMISSION_RECONCILIATION_REQUIRED"
    summary={"stage":"US1_INTEGRATION_EVIDENCE_GATE","status":status,"head":"ce9018c","membership_source":"wikipedia_secondary+ishares_IVV_institutional","ivv_as_of":ivv_asof,"admitted_reviewed":len(adm),"membership_verified":sum(1 for r in matrix if r["Membership"]=="MEMBERSHIP_VERIFIED"),"membership_conflict":sum(1 for r in matrix if r["Membership"]=="MEMBERSHIP_CONFLICT"),"identity_pass":sum(1 for r in matrix if r["Identity"]=="PASS"),"instrument_pass":len(adm),"canonical_pass":len(can),"history_pass":sum(1 for r in elig if r["History_State"]=="PASS"),"liquidity_pass":sum(1 for r in elig if r["Liquidity_Class"] in {"PREFERRED","STANDARD"}),"eligible":sum(1 for r in elig if r["Eligibility_DryRun"]=="ELIGIBLE"),"integration_ready":len(a_rows),"evidence_review":cls.get("B",0),"data_repair_required":cls.get("C",0),"admission_review":cls.get("D",0)+len(rev),"not_eligible":cls.get("E",0),"excluded":cls.get("F",0),"review_104":dict(Counter(r["Review_Category"] for r in rev_out)),"hona":"NOT_ELIGIBLE_HISTORY_FAIL_NOT_REPAIRABLE","research_partial":1633,"strict":759,"frozen":0,"us_in_1633":0,"universe_write":False,"next_action":"STOP_MANAGER_GATE","class_counts_admitted":dict(cls),"as_of_utc":ASOF}
    json.dump(summary, open(OUT/"summary_us1_integration_gate.json","w",encoding="utf-8"), indent=2)
    md="# US-1 Integration Evidence Gate\nHEAD ce9018c. Write NO.\nSTATUS: %s\nA=%s B=%s E=%s REVIEW=%s HONA=E\n1633/759/0 STOP\n"%(status,len(a_rows),cls.get("B",0),cls.get("E",0),len(rev))
    (ROOT/"docs"/"spec"/"US1_Integration_Evidence_Gate_Report.md").write_text(md, encoding="utf-8")
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
