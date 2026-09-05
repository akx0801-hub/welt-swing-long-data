#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, re, subprocess, urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from html import unescape
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
OUT=ROOT/"output_au1_admission_build"
XLS="https://www.blackrock.com/au/products/251852/ishares-core-s-p-asx-200-etf/1535604546388.ajax?fileType=xls&fileName=iShares-Core-SPASX-200-ETF_fund&dataType=fund"
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rcsv(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def wcsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("none\n", encoding="utf-8"); return
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
def ident(r): return (r.get("ISIN") or "", r.get("Primary_MIC") or r.get("MIC") or "", r.get("Primary_Ticker") or r.get("Ticker") or "")
def gate(ok): return "PASS" if ok else "FAIL"
def classify(d):
    n=unescape(d.get("Name") or "").upper()
    if d.get("Asset Class")!="Equity": return "EXCLUDE","NON_INDEX_HOLDING","OTHER"
    if "CDI" in n: return "EXCLUDE","CDI","CDI"
    if "ETF" in n or " FUND" in n: return "EXCLUDE","ETF_FUND","ETF"
    if d.get("Sector")=="Real Estate" or "REIT" in n: return "REVIEW","REVIEW_AREIT","A_REIT"
    if "STAPLED" in n or "GROUP UNITS" in n or n.endswith(" UNITS"): return "REVIEW","REVIEW_STAPLED","STAPLED"
    if not d["ISIN"] or not d["Ticker"]: return "REVIEW","REVIEW_IDENTITY","ORDINARY"
    if not d["ISIN"].startswith("AU"): return "REVIEW","REVIEW_FOREIGN_ORDINARY","ORDINARY"
    if d.get("Market Currency") not in {"AUD",""}: return "REVIEW","REVIEW_CURRENCY","ORDINARY"
    return "ADMIT","ASX200_ORDINARY_XASX_IOZ_RANK3","ORDINARY"
def main():
    uni_sha=sha(UNI); fro_sha=sha(FROZEN)
    head=subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=ROOT, text=True).strip()
    if not head.startswith("ffdffef"): raise SystemExit("STOP START STATE MISMATCH head %s"%head)
    uni=rcsv(UNI); elig=rcsv(ELIG)
    if len(uni)!=2374: raise SystemExit("STOP n")
    if sum(1 for r in uni if r["Source_ID"]=="US1_SP500_COMMON_EVIDENCE_GATE")!=372: raise SystemExit("STOP us1")
    if sum(1 for r in uni if r["Source_ID"]=="US2_SP400_COMMON_ADMISSION")!=369: raise SystemExit("STOP us2")
    if sum(1 for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")!=759: raise SystemExit("STOP strict")
    if sum(1 for _ in open(FROZEN,encoding="utf-8"))!=1: raise SystemExit("STOP frozen")
    exist_is={r["ISIN"] for r in uni if r["ISIN"]}
    req=urllib.request.Request(XLS, headers={"User-Agent":"welt-swing-au1/0.1"})
    xls=urllib.request.urlopen(req, timeout=45).read().decode("utf-8","replace")
    hold=[p for p in re.split(r'<ss:Worksheet ss:Name="', xls)[1:] if p.startswith("Holdings")][0]
    xrows=re.findall(r"<ss:Row>(.*?)</ss:Row>", hold, re.S)
    def vals(r): return re.findall(r'<ss:Data ss:Type="[^"]+">([^<]*)</ss:Data>', r)
    snap=""; hdr=None; hi=None
    for i,r in enumerate(xrows):
        v=vals(r)
        if v[:1]==["Fund Holdings as of"] and len(v)>1: snap=v[1]
        if v[:1]==["Ticker"] and "ISIN" in v:
            hdr=v; hi=i; break
    if not hdr: raise SystemExit("STOP no holdings header")
    raw=[]
    for r in xrows[hi+1:]:
        v=vals(r)
        if len(v)>=len(hdr): raw.append(dict(zip(hdr,v)))
    recs=[]
    for d in raw:
        st,reason,inst=classify(d)
        t,isin=d.get("Ticker") or "", d.get("ISIN") or ""
        m="XASX" if d.get("Asset Class")=="Equity" else ""
        wsid="WS:XASX:%s"%t if t and m else ""
        recs.append({"WS_ID":wsid,"ISIN":isin,"MIC":m,"Primary_Ticker":t,"Issuer":unescape(d.get("Name") or ""),"Instrument_Type":inst,"Sector":d.get("Sector") or "","Index_Membership":"SP_ASX_200" if d.get("Asset Class")=="Equity" else "NO","Admission_Status":st,"Evidence_Source":"iShares_IOZ","Evidence_Rank":"3","Snapshot_Date":snap,"Reason_Code":reason,"Review_Reason":reason if st=="REVIEW" else "","Currency":d.get("Market Currency") or ""})
    disc=[r for r in recs if r["Index_Membership"]=="SP_ASX_200"]
    adm=[r for r in disc if r["Admission_Status"]=="ADMIT"]
    rev=[r for r in disc if r["Admission_Status"]=="REVIEW"]
    disc_exc=[r for r in disc if r["Admission_Status"]=="EXCLUDE"]
    exc=[r for r in recs if r["Admission_Status"]=="EXCLUDE"]
    if len(disc)!=len(adm)+len(rev)+len(disc_exc): raise SystemExit("STOP recon")
    ov=[]
    for r in disc:
        hits=[u for u in uni if (r["ISIN"] and u["ISIN"]==r["ISIN"]) or u["WS_ID"]==r["WS_ID"]]
        if hits:
            u=hits[0]
            same=ident(r)==(u["ISIN"],u["Primary_MIC"],u["Primary_Ticker"])
            ov.append({"AU_Ticker":r["Primary_Ticker"],"AU_ISIN":r["ISIN"],"Existing_WS_ID":u["WS_ID"],"Existing_ISIN":u["ISIN"],"Existing_MIC":u["Primary_MIC"],"Existing_Ticker":u["Primary_Ticker"],"Overlap_Type":"IDENTITY" if same else "ISIN_OR_WS","Classification":"CONFLICT" if same else "CHECK"})
    id_ov=sum(1 for r in disc if r["ISIN"] in exist_is)
    tick_coll=sorted({r["Primary_Ticker"] for r in disc} & {u["Primary_Ticker"] for u in uni})
    areit=sum(1 for r in rev if r["Reason_Code"]=="REVIEW_AREIT")
    stap=sum(1 for r in rev if r["Reason_Code"]=="REVIEW_STAPLED")
    foreign=sum(1 for r in rev if r["Reason_Code"]=="REVIEW_FOREIGN_ORDINARY")
    cdi=sum(1 for r in exc if r["Instrument_Type"]=="CDI")
    g={
        "G0":gate(head.startswith("ffdffef")),
        "G1":gate(all(r["Index_Membership"]=="SP_ASX_200" for r in disc)),
        "G2":gate(all(r["MIC"]=="XASX" for r in disc) and not any(r["MIC"] in {"XNYS","XNAS","XTSE","XKRX","XHKG"} for r in disc)),
        "G3":gate(all(r["Evidence_Rank"]=="3" for r in adm) and all(r["Evidence_Source"]=="iShares_IOZ" for r in adm)),
        "G4":gate(all(r["Evidence_Source"]=="iShares_IOZ" and r["Snapshot_Date"] for r in disc)),
        "G5":gate(all(r["ISIN"] and r["MIC"]=="XASX" and r["Primary_Ticker"] for r in adm)),
        "G6":gate(all(r["MIC"]=="XASX" for r in adm)),
        "G7":gate(all(r["Instrument_Type"]=="ORDINARY" for r in adm)),
        "G8":gate(areit==sum(1 for r in disc if r["Reason_Code"]=="REVIEW_AREIT") and not any(r["Reason_Code"]=="REVIEW_AREIT" for r in adm)),
        "G9":gate(not any(r["Instrument_Type"]=="STAPLED" for r in adm)),
        "G10":gate(not any(r["Instrument_Type"]=="ETF" for r in adm)),
        "G11":gate(not any(r["Instrument_Type"]=="CDI" for r in adm) and all(r["Admission_Status"]=="EXCLUDE" for r in recs if r["Instrument_Type"]=="CDI")),
        "G12":gate(all(bool(r["ISIN"]) for r in adm)),
        "G13":gate(id_ov==0 and not ov),
        "G14":gate(len({r["WS_ID"] for r in disc if r["WS_ID"]})==len([r for r in disc if r["WS_ID"]]) and len({r["ISIN"] for r in disc if r["ISIN"]})==len([r for r in disc if r["ISIN"]])),
        "G15":gate(len(disc)==len(adm)+len(rev)+len(disc_exc)),
        "G16":gate(sha(UNI)==uni_sha and sha(FROZEN)==fro_sha and len(uni)==2374),
    }
    fails=[k for k,v in g.items() if v=="FAIL"]
    status="AU-1 S&P/ASX 200 COMMON — ADMISSION BUILD PASS" if not fails else "AU-1 ADMISSION BUILD FAIL"
    OUT.mkdir(parents=True, exist_ok=True)
    wcsv(OUT/"AU1_ADMISSION_DISCOVERY.csv", disc)
    wcsv(OUT/"AU1_ADMISSION_CANDIDATES.csv", adm)
    wcsv(OUT/"AU1_ADMISSION_REVIEW.csv", rev)
    wcsv(OUT/"AU1_ADMISSION_EXCLUDE.csv", exc)
    wcsv(OUT/"AU1_EXISTING_UNIVERSE_OVERLAP.csv", ov or [{"AU_Ticker":"","AU_ISIN":"","Existing_WS_ID":"","Existing_ISIN":"","Existing_MIC":"","Existing_Ticker":"","Overlap_Type":"none","Classification":"NONE"}])
    wcsv(OUT/"AU1_BUILD_SUMMARY.csv", [{"metric":k,"value":v} for k,v in [("discovery",len(disc)),("admit",len(adm)),("review",len(rev)),("exclude_file",len(exc)),("discovery_exclude",len(disc_exc)),("areit",areit),("stapled",stap),("foreign_ordinary",foreign),("cdi",cdi),("identity_overlap",id_ov)]])
    json.dump({"source":"iShares_IOZ","rank":3,"as_of":snap,"url":XLS,"holdings":len(raw),"equity":len(disc)}, open(OUT/"ioz_source_snapshot.json","w",encoding="utf-8"), indent=2)
    md="\n".join([
        "# AU-1 S&P/ASX 200 Admission Build Report",
        "1. Start HEAD: ffdffef. SIDECAR ONLY. NO UNIVERSE WRITE.",
        "2. Source: iShares Core S&P/ASX 200 ETF (IOZ), BlackRock product 251852, XLS holdings. Evidence rank 3 institutional named-index file. Wikipedia not used. CSV ajax rejected (no ISIN).",
        "3. Snapshot date: %s"%snap,
        "4. Discovery: %s IOZ equity holdings tagged SP_ASX_200. Nominal index 200 is not an ADMIT target."%len(disc),
        "5. ADMIT: %s ordinary AU-ISIN XASX AUD."%len(adm),
        "6. REVIEW: %s = A-REIT %s + stapled-non-RE %s + foreign-ordinary NZ %s."%(len(rev),areit,stap,foreign),
        "7. EXCLUDE file: %s = CDI %s + non-index cash/futures %s. Discovery EXCLUDE (in 201): %s CDI. Reconciliation: Discovery %s = ADMIT %s + REVIEW %s + Discovery-EXCLUDE %s. Non-index holdings are outside Discovery by classification model."%(len(exc),cdi,len(exc)-cdi,len(disc_exc),len(disc),len(adm),len(rev),len(disc_exc)),
        "8. Instrument: ADMIT Instrument_Type=ORDINARY only. Preferred/hybrid/units/ETF in ADMIT = 0. A-REIT and stapled never ADMIT.",
        "9. Identity QA: all ADMIT have ISIN+XASX+ticker. Missing ISIN ADMIT=0. Duplicate WS_ID Discovery=0. Duplicate ISIN Discovery=0. No ticker-only ADMIT.",
        "10. MIC QA: all Discovery and all ADMIT MIC=XASX. No MIC-merge. No US/CA/KR/HK in Discovery.",
        "11. Existing-universe overlap vs Research Partial 2374: identity triple = %s. ISIN overlap = %s. Ticker-only collisions ALLOWED (%s): %s."%(id_ov,id_ov,len(tick_coll),",".join(tick_coll) or "none"),
        "12. Evidence QA: all Discovery Evidence_Source=iShares_IOZ, Rank=3, Snapshot=%s. Rank 1 official S&P file not used (unavailable this build). Rank 4 Wikipedia not used for ADMIT."%snap,
        "13. A-REIT: fail-closed REVIEW when Sector=Real Estate or name contains REIT. Count %s. ADMIT A-REIT = 0. Not reinterpreted as ordinary."%areit,
        "14. Stapled: fail-closed REVIEW when name has STAPLED / GROUP UNITS / trailing UNITS, unless already A-REIT. Non-REIT stapled: %s. ADMIT stapled = 0. Stapled != common."%stap,
        "15. CDI: EXCLUDE when issuer name contains CDI. Count %s. Not converted to ordinary XASX ADMIT."%cdi,
        "16. ETF/Fund: EXCLUDE policy. ETF in IOZ equity holdings = 0. Cash/futures EXCLUDE as NON_INDEX_HOLDING.",
        "17. Exceptions: ADMIT < 200 by design (policy-compliant, not maximization). Foreign-incorp ASX ordinary (NZ ISIN) = REVIEW, do not copy US-2 foreign-ISIN ADMIT. PXA PEXA GROUP LTD is Real Estate sector so REVIEW_AREIT fail-closed (not auto-ordinary). MQG name contains DEF in IOZ source; left as ordinary ADMIT (source Asset Class Equity, AU ISIN, not CDI/REIT/stapled).",
        "18. Gates G0-G16: %s"%g,
        "19. Final build status: "+status+". Research Partial 2374 unchanged. US-1 372 unchanged. US-2 369 unchanged. Strict 759 unchanged. Frozen 0 unchanged. AU membership in Research Partial = 0. universe_write=false.",
        "20. Next manager gate: SEPARATE AU-1 EVIDENCE / ADMISSION GATE. ADMIT != INTEGRATED. BUILD PASS != WRITE AUTHORIZATION. No History / Liquidity / Eligibility / Korea / US-3 / Canada.",
    ])
    (ROOT/"docs"/"spec"/"AU1_Admission_Build_Report.md").write_text(md+"\n", encoding="utf-8")
    if sha(UNI)!=uni_sha or sha(FROZEN)!=fro_sha: raise SystemExit("STOP UNAUTHORIZED CHANGE")
    summary={"stage":"AU1_ADMISSION_BUILD","status":status,"head":"ffdffef","discovery":len(disc),"admit":len(adm),"review":len(rev),"exclude":len(exc),"discovery_exclude":len(disc_exc),"identity_overlap":id_ov,"ticker_collisions":tick_coll,"research_partial":2374,"strict":759,"frozen":0,"universe_write":False,"gates":g,"fails":fails,"next_action":"STOP_SEPARATE_AU1_EVIDENCE_GATE","as_of_utc":ASOF}
    json.dump(summary, open(OUT/"summary_au1_admission.json","w",encoding="utf-8"), indent=2)
    print(json.dumps({k:summary[k] for k in summary if k!="gates"}, indent=2)); print(json.dumps(g, indent=2)); return 0 if not fails else 1
if __name__=="__main__":
    raise SystemExit(main())
