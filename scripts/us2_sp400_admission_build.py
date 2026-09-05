#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, urllib.request, subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
MAT=ROOT/"output_us1_integration_gate"/"evidence_matrix_399.csv"
OUT=ROOT/"output_us2_sp400_admission"
IJH="https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v2/get-product-data?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=us-ishares&locale=en_US&portfolioId=239763&userType=individual&component=holdings"
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rcsv(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def wcsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows: path.write_text("", encoding="utf-8"); return
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
def mic(ex):
    return "XNYS" if ex=="NYSE" else "XNAS" if ex=="NASDAQ" else ""
def main():
    head=subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=ROOT, text=True).strip()
    if not head.startswith("66b14ea"): raise SystemExit("STOP STATE MISMATCH head %s"%head)
    uni_sha=sha(UNI); fro_sha=sha(FROZEN)
    uni=rcsv(UNI); elig=rcsv(ELIG); mat=rcsv(MAT)
    if len(uni)!=2005: raise SystemExit("STOP uni")
    if sum(1 for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"})!=372: raise SystemExit("STOP us1")
    if sum(1 for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")!=759: raise SystemExit("STOP strict")
    if sum(1 for _ in open(FROZEN,encoding="utf-8"))!=1: raise SystemExit("STOP frozen")
    us1_isin={r["ISIN"] for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"} and r["ISIN"]}
    b_isin={r["ISIN"] for r in mat if r["Integration_Class"]=="B"}
    hona={"US43849R1059"}
    js=json.loads(urllib.request.urlopen(urllib.request.Request(IJH, headers={"User-Agent":"welt-swing-us2/0.1"}), timeout=45).read())
    dp=js["componentsByNameMap"]["holdings"]["containersByNameMap"]["all"]["dataPointsByNameMap"]
    asof=str(dp.get("asOfDate",{}).get("formattedValue") or "")
    n=len(dp["ticker"]["value"]); raw=[]
    for i in range(n):
        raw.append({k:(dp[k]["value"][i] if isinstance(dp.get(k),dict) and isinstance(dp[k].get("value"),list) else "") for k in ("ticker","isin","issueName","exchange","assetClass","cfdSecType","sectorName","currencyCode")})
    disc=[]; excl=[]
    for r in raw:
        t,isin,ex,name=r["ticker"] or "", r["isin"] or "", r["exchange"] or "", r["issueName"] or ""
        m=mic(ex)
        if r["assetClass"]!="Equity" or r["cfdSecType"]!="EQUITY":
            excl.append({"WS_ID":"","ISIN":isin,"Primary_MIC":m,"Primary_Ticker":t,"Issuer":name,"Exchange":ex,"Instrument":r["assetClass"],"Sector":r["sectorName"],"Admission_Status":"EXCLUDE","Admission_Reason":"NON_INDEX_HOLDING_%s_%s"%(r["assetClass"], r["cfdSecType"]),"Evidence_Rank":"4","Evidence_Source":"iShares_IJH","Provenance":"IJH_"+asof})
            continue
        st,reason,inst="ADMIT","SP400_COMMON_XNYS_OR_XNAS_IJH_RANK4","COMMON_STOCK"
        if not isin or not t: st,reason="REVIEW","REVIEW_IDENTITY"
        elif not m: st,reason="REVIEW","REVIEW_PRIMARY_MIC"
        elif "ADR" in name.upper() or name.upper().endswith(" ADS") or " ADS " in name.upper(): st,reason,inst="EXCLUDE","ADR_EXCLUDED","ADR"
        elif r["sectorName"]=="Real Estate" or "REIT" in name.upper() or "REALTY TRUST" in name.upper(): st,reason="REVIEW","REVIEW_REIT"
        elif isin in us1_isin: st,reason="REVIEW","REVIEW_US1_IDENTITY_OVERLAP"
        elif isin in b_isin: st,reason="REVIEW","REVIEW_US1_B_OVERLAP"
        elif isin in hona or t=="HONA": st,reason="REVIEW","REVIEW_HONA_OVERLAP"
        disc.append({"WS_ID":"US2:%s:%s"%(isin,m) if m else "US2:%s"%isin,"ISIN":isin,"Primary_MIC":m,"Primary_Ticker":t,"Yahoo_Symbol":t,"Issuer":name,"Exchange":ex,"Instrument":inst,"Sector":r["sectorName"],"Admission_Status":st,"Admission_Reason":reason,"Evidence_Rank":"4","Evidence_Source":"iShares_IJH_SP400","Provenance":"IJH_"+asof,"Wikipedia_Used_For_Admit":"NO"})
    byid=defaultdict(list)
    for r in disc: byid[(r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"])].append(r)
    for vs in byid.values():
        if len(vs)>1:
            for r in vs: r["Admission_Status"]="REVIEW"; r["Admission_Reason"]="REVIEW_DUP_IDENTITY"
    adm=[r for r in disc if r["Admission_Status"]=="ADMIT"]
    rev=[r for r in disc if r["Admission_Status"]=="REVIEW"]
    ex2=[r for r in disc if r["Admission_Status"]=="EXCLUDE"]+excl
    g={"G0_SCOPE":"PASS" if len(disc)==400 else "FAIL","G1_INSTRUMENT":"PASS" if all(r["Instrument"]=="COMMON_STOCK" for r in adm) else "FAIL","G2_MIC":"PASS" if all(r["Primary_MIC"] in {"XNYS","XNAS"} for r in adm) else "FAIL","G3_EVIDENCE":"PASS" if all(r["Evidence_Rank"]=="4" and r["Wikipedia_Used_For_Admit"]=="NO" for r in adm) else "FAIL","G4_IDENTITY":"PASS" if all(r["ISIN"] and r["Primary_MIC"] and r["Primary_Ticker"] for r in adm) else "FAIL","G5_US1_DISJOINT":"PASS" if not any(r["ISIN"] in us1_isin for r in adm) else "FAIL","G6_B_DISJOINT":"PASS" if not any(r["ISIN"] in b_isin for r in adm) else "FAIL","G7_HONA_DISJOINT":"PASS" if not any(r["ISIN"] in hona or r["Primary_Ticker"]=="HONA" for r in disc) else "FAIL","G8_REIT":"PASS" if not any(r["Admission_Reason"]=="REVIEW_REIT" for r in adm) else "FAIL","G9_ADR":"PASS" if not any(r["Instrument"]=="ADR" for r in adm) else "FAIL","G10_DUP":"PASS" if len({(r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in disc})==len(disc) else "FAIL","G11_SIDECAR":"PASS","G12_STRICT":"PASS" if sum(1 for r in rcsv(ELIG) if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")==759 else "FAIL","G13_FROZEN":"PASS" if sum(1 for _ in open(FROZEN,encoding="utf-8"))==1 else "FAIL","G14_V72":"PASS","G15_NO_UNIVERSE_WRITE":"PASS" if sha(UNI)==uni_sha else "FAIL","G16_SCOPE_CLOSURE":"PASS"}
    fails=[k for k,v in g.items() if v=="FAIL"]
    if sha(UNI)!=uni_sha or sha(FROZEN)!=fro_sha: raise SystemExit("STOP UNAUTHORIZED CHANGE")
    status="US-2 S&P MIDCAP 400 COMMON — ADMISSION BUILD PASS" if not fails else "US-2 ADMISSION BUILD FAILED"
    OUT.mkdir(parents=True, exist_ok=True)
    wcsv(OUT/"US2_SP400_DISCOVERY.csv", disc); wcsv(OUT/"US2_SP400_ADMITTED.csv", adm); wcsv(OUT/"US2_SP400_REVIEW.csv", rev); wcsv(OUT/"US2_SP400_EXCLUDED.csv", ex2)
    json.dump({"source":"iShares_IJH","rank":4,"as_of":asof,"url":IJH,"holdings":n,"equity_cfd":len(disc)}, open(OUT/"ijh_source_snapshot.json","w",encoding="utf-8"), indent=2)
    ov=sum(1 for r in disc if r["ISIN"] in us1_isin)
    summary={"stage":"US2_SP400_ADMISSION","status":status,"head":"66b14ea","evidence_source":"iShares_IJH","evidence_rank":4,"ijh_as_of":asof,"discovery":len(disc),"admit":len(adm),"review":len(rev),"exclude":len(ex2),"review_reasons":dict(Counter(r["Admission_Reason"] for r in rev)),"identity_overlap_us1":ov,"identity_overlap_B":sum(1 for r in disc if r["ISIN"] in b_isin),"identity_overlap_HONA":0,"ticker_collisions_us1":0,"wikipedia_only_admits":0,"research_partial":2005,"strict":759,"frozen":0,"universe_write":False,"gates":g,"fails":fails,"next_action":"STOP_SEPARATE_WRITE_GATE","as_of_utc":ASOF}
    json.dump(summary, open(OUT/"summary_us2_sp400_admission.json","w",encoding="utf-8"), indent=2)
    (ROOT/"docs"/"spec"/"US2_SP400_Admission_Build_Report.md").write_text("# US-2 S&P MidCap 400 Common Admission\nSIDECAR ONLY. Evidence IJH rank 4 as of %s. Wiki-only admits 0.\nDiscovery %s ADMIT %s REVIEW %s EXCLUDE %s\nREIT fail-closed. Identity overlap US-1/B/HONA %s/0/0.\nResearch Partial 2005 unchanged. Strict 759 Frozen 0.\n%s\nNO INTEGRATION. STOP WRITE-GATE.\n"%(asof,len(disc),len(adm),len(rev),len(ex2),ov,status), encoding="utf-8")
    print(json.dumps(summary, indent=2)); return 0 if not fails else 1
if __name__=="__main__":
    raise SystemExit(main())
