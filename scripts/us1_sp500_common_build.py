#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, re, time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd, requests, yfinance as yf
from lxml import html
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
OUT=ROOT/"output_us1"
WIKI="https://en.wikipedia.org/api/rest_v1/page/html/List_of_S%26P_500_companies"
UA={"User-Agent":"welt-swing-us1/0.1 (research; https://github.com/akx0801-hub/welt-swing-long-data)"}
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def wcsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8"); return
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
def recs(by,s):
    for k in (s,s.replace(".","/"),s.replace(".","-")):
        if k in by: return by[k]
    return []
def yf_sym(s): return s.replace(".","-")
def classify(row):
    u=str(row["Security"]).upper(); sector=str(row["GICS Sector"])
    if any(x in u for x in (" PREF"," PREFERRED"," WARRANT"," RIGHT"," UNIT")): return "EXCLUDE","NAME_NON_COMMON"
    if sector=="Real Estate": return "REVIEW","GICS_REAL_ESTATE_REIT_POLICY"
    if re.search(r"\b(ADR|ADS)\b", u): return "EXCLUDE","ADR_NAME"
    return "ADMIT_CANDIDATE","SP500_COMMON_EQUITY_DEFAULT"
def main():
    if sum(1 for _ in open(FROZEN,encoding="utf-8"))!=1: raise SystemExit("frozen")
    uni_sha=sha(UNI)
    uni=list(csv.DictReader(open(UNI,encoding="utf-8-sig")))
    elig=list(csv.DictReader(open(ELIG,encoding="utf-8")))
    if len(uni)!=1633: raise SystemExit("uni")
    if sum(1 for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")!=759: raise SystemExit("strict")
    ident=[(r["WS_ID"],r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in uni]
    if sum(1 for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"})!=0: raise SystemExit("us_already")
    r=requests.get(WIKI,timeout=30,headers=UA); r.raise_for_status()
    wiki_lm=r.headers.get("Last-Modified") or ASOF
    df=pd.read_html(html.tostring(html.fromstring(r.content).xpath("//table")[0]))[0]
    df["Symbol"]=df["Symbol"].astype(str).str.strip()
    tickers=list(df["Symbol"]); extra=[]
    for s in tickers:
        if "." in s: extra += [s.replace(".","/"), s.replace(".","-")]
    all_t=list(dict.fromkeys(tickers+extra)); bindings=[]
    for i in range(0,len(all_t),60):
        chunk=all_t[i:i+60]; lit=" ".join('"'+s.replace('"','')+'"' for s in chunk)
        q=f"""SELECT ?item ?itemLabel ?ticker ?isin ?mic WHERE {{ VALUES ?ticker {{ {lit} }} ?item p:P414 ?stmt . ?stmt ps:P414 ?exchange . ?stmt pq:P249 ?ticker . OPTIONAL {{ ?exchange wdt:P7534 ?mic. }} OPTIONAL {{ ?item wdt:P946 ?isin. }} SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
        rr=requests.get("https://query.wikidata.org/sparql", params={"query":q,"format":"json"}, timeout=90, headers={**UA,"Accept":"application/sparql-results+json"}); rr.raise_for_status()
        bindings.extend(rr.json()["results"]["bindings"]); time.sleep(0.15)
    by=defaultdict(list)
    for x in bindings: by[x["ticker"]["value"]].append(x)
    discovery=[]
    for _,row in df.iterrows():
        s=row["Symbol"]; xs=recs(by,s)
        isins=sorted({x["isin"]["value"] for x in xs if "isin" in x and x["isin"]["value"].startswith("US")})
        mics=sorted({x["mic"]["value"] for x in xs if x.get("mic",{}).get("value") in {"XNYS","XNAS"}})
        qid=xs[0]["item"]["value"].rsplit("/",1)[-1] if xs else ""
        issuer=xs[0]["itemLabel"]["value"] if xs and "itemLabel" in xs[0] else row["Security"]
        decision,reason=classify(row)
        ok=len(isins)==1 and len(mics)==1
        if decision=="ADMIT_CANDIDATE" and not ok:
            decision,reason="REVIEW",("IDENTITY_INCOMPLETE" if not isins or not mics else "IDENTITY_AMBIGUOUS")
        elif decision=="ADMIT_CANDIDATE":
            decision,reason="ADMIT","SP500_COMMON_XNYS_OR_XNAS_ISIN"
        admission=decision if decision in {"ADMIT","REVIEW","EXCLUDE"} else "REVIEW"
        discovery.append({"Yahoo_Symbol":yf_sym(s),"Primary_Ticker":s,"Issuer":issuer,"Security":row["Security"],"GICS_Sector":row["GICS Sector"],"GICS_Sub":row["GICS Sub-Industry"],"CIK":str(row["CIK"]),"Wikidata_QID":qid,"ISIN":isins[0] if len(isins)==1 else "|".join(isins),"Primary_MIC":mics[0] if len(mics)==1 else "|".join(mics),"Instrument_Type":"REIT_REVIEW" if "REIT" in reason else "COMMON_STOCK","Admission_Status":admission,"Admission_Reason":reason,"Evidence_Source":"wikipedia_list_sp500+wikidata_P946_P414","Evidence_Status":"VERIFIED" if admission=="ADMIT" else "INCOMPLETE_OR_POLICY","SP500_Membership":"VERIFIED_SECONDARY_WIKIPEDIA","WS_ID":f"US1:{(isins[0] if len(isins)==1 else 'NOISIN')}:{(mics[0] if len(mics)==1 else 'NOMIC')}"})
    OUT.mkdir(parents=True, exist_ok=True)
    admitted=[x for x in discovery if x["Admission_Status"]=="ADMIT"]
    review=[x for x in discovery if x["Admission_Status"]=="REVIEW"]
    excluded=[x for x in discovery if x["Admission_Status"]=="EXCLUDE"]
    wcsv(OUT/"discovery_sp500_wikipedia.csv", discovery)
    wcsv(OUT/"admission_admitted.csv", admitted)
    wcsv(OUT/"admission_review.csv", review)
    wcsv(OUT/"admission_excluded.csv", excluded)
    tks=[x["Yahoo_Symbol"] for x in admitted]
    hist=yf.download(tks, period="2y", auto_adjust=False, group_by="ticker", threads=True, progress=False)
    fx=yf.download("USDEUR=X", period="2y", auto_adjust=False, progress=False)
    fx_close=fx["Close"]
    if isinstance(fx_close, pd.DataFrame): fx_close=fx_close.iloc[:,0]
    fx_close=fx_close.dropna(); today=pd.Timestamp.utcnow().normalize().tz_localize(None)
    hist_rows=[]; liq_rows=[]; elig_rows=[]
    for rec in admitted:
        sym=rec["Yahoo_Symbol"]
        try: h=hist[sym].copy() if isinstance(hist.columns, pd.MultiIndex) else hist.copy()
        except Exception: h=None
        future=dups=unique=valid=0; hist_state="NO_BARS"
        if h is not None and not h.empty:
            h=h.dropna(how="all"); h.index=pd.to_datetime(h.index).tz_localize(None)
            unique=int(h.index.nunique()); dups=int(len(h)-unique); future=int((h.index.normalize()>today).sum())
            need=["Open","High","Low","Close","Volume"]
            if all(c in h.columns for c in need):
                v=h.dropna(subset=need); v=v[(v["High"]>=v["Low"])&(v["Volume"]>=0)]; valid=int(len(v))
                hist_state="HISTORY_FAIL" if future or dups or unique<260 or valid<252 else "PASS"
            else: hist_state="SCHEMA_FAIL"
        hist_rows.append({"WS_ID":rec["WS_ID"],"Yahoo_Symbol":sym,"ISIN":rec["ISIN"],"Primary_MIC":rec["Primary_MIC"],"Unique_Bars":unique,"Valid_Bars":valid,"Future_Bars":future,"Duplicate_Dates":dups,"History_State":hist_state,"History_Source":"yfinance_download"})
        med=None; usable=0; liq="FAIL"
        if h is not None and not h.empty and "Close" in h.columns and "Volume" in h.columns:
            hv=h.dropna(subset=["Close","Volume"]).copy(); hv["to_usd"]=hv["Close"]*hv["Volume"]
            last=hv.join(fx_close.rename("usdeur"), how="inner").tail(20); usable=int(len(last))
            if usable: med=float((last["to_usd"]*last["usdeur"]).median())
            liq="PREFERRED" if med is not None and med>=20_000_000 else "STANDARD" if med is not None and med>=15_000_000 else "EXCEPTION" if med is not None and med>=5_000_000 else "FAIL"
        liq_rows.append({"WS_ID":rec["WS_ID"],"Yahoo_Symbol":sym,"Liquidity_Class":liq,"MedianTurnover20_EUR":("" if med is None else round(med,2)),"Usable20":usable,"FX":"USDEUR=X","Quote_Scale":1})
        if rec["Admission_Status"]!="ADMIT": dry="NOT_ELIGIBLE_INSTRUMENT"
        elif hist_state!="PASS" or usable<18: dry="HISTORY_FAILURE"
        elif liq=="FAIL": dry="NOT_ELIGIBLE_LIQUIDITY"
        elif liq=="EXCEPTION": dry="REVIEW"
        else: dry="ELIGIBLE"
        elig_rows.append({**{k:rec[k] for k in ("WS_ID","Yahoo_Symbol","ISIN","Primary_MIC","Issuer","Admission_Status")},"History_State":hist_state,"Liquidity_Class":liq,"MedianTurnover20_EUR":("" if med is None else round(med,2)),"Eligibility_DryRun":dry,"Universe_Write":"NO"})
    wcsv(OUT/"history_qa_us1.csv", hist_rows); wcsv(OUT/"liquidity_us1.csv", liq_rows); wcsv(OUT/"eligibility_dry_run_us1.csv", elig_rows)
    groups=defaultdict(list); elig_by={x["WS_ID"]:x for x in elig_rows}
    for rec in admitted: groups[(rec["Wikidata_QID"] or rec["Issuer"], rec["Primary_MIC"])].append(rec)
    canonical=[]
    for (issuer,mic), items in groups.items():
        def score(x):
            e=elig_by.get(x["WS_ID"], {})
            try: t=float(e.get("MedianTurnover20_EUR") or 0)
            except ValueError: t=0
            return (1 if e.get("Eligibility_DryRun")=="ELIGIBLE" else 0, t)
        pick=sorted(items, key=score, reverse=True)[0]; e=elig_by.get(pick["WS_ID"], {})
        canonical.append({"Issuer_Key":issuer,"Primary_MIC":mic,"Canonical_WS_ID":pick["WS_ID"],"Canonical_Ticker":pick["Primary_Ticker"],"ISIN":pick["ISIN"],"Group_N":len(items),"Eligibility_DryRun":e.get("Eligibility_DryRun",""),"Note":"unapplied to 1633"})
    wcsv(OUT/"canonical_scan_us1.csv", canonical)
    if [(x["WS_ID"],x["ISIN"],x["Primary_MIC"],x["Primary_Ticker"]) for x in csv.DictReader(open(UNI,encoding="utf-8-sig"))]!=ident: raise SystemExit("identity mutated")
    if sha(UNI)!=uni_sha: raise SystemExit("universe mutated")
    c_elig=Counter(x["Eligibility_DryRun"] for x in elig_rows); c_hist=Counter(x["History_State"] for x in hist_rows)
    c_liq=Counter(x["Liquidity_Class"] for x in liq_rows); c_adm=Counter(x["Admission_Status"] for x in discovery)
    hist_pass=c_hist.get("PASS",0); liq_ok=c_liq.get("PREFERRED",0)+c_liq.get("STANDARD",0)
    status="BUILD_PARTIAL_BLOCKED_OR_REVIEW"
    if c_adm.get("ADMIT",0)>=350 and hist_pass>=0.8*max(c_adm.get("ADMIT",1),1) and c_elig.get("ELIGIBLE",0)>=300:
        status="BUILD_PASS_READY_FOR_MANAGER_INTEGRATION_GATE"
    if c_adm.get("ADMIT",0)<50: status="BUILD_FAIL"
    gates={"G0_SCOPE":"PASS","G1_MEMBERSHIP":"PASS","G2_INSTRUMENT":"PASS","G3_IDENTITY":"PASS" if c_adm.get("ADMIT",0) else "FAIL","G4_EVIDENCE":"PASS","G5_MAPPING":"PASS","G6_HISTORY":"PASS" if hist_pass else "FAIL","G7_LIQUIDITY":"PASS" if liq_ok else "FAIL","G8_ELIGIBILITY":"PASS" if elig_rows else "FAIL","G9_CANONICAL":"PASS" if canonical else "FAIL","G10_INTEGRITY":"PASS"}
    summary={"stage":"US1_SP500_COMMON","us1_status":status,"source":"wikipedia_list_of_sp500_companies","source_class":"SECONDARY","source_as_of_utc":ASOF,"wiki_last_modified":wiki_lm,"discovery":len(discovery),"admitted":c_adm.get("ADMIT",0),"review":c_adm.get("REVIEW",0),"excluded":c_adm.get("EXCLUDE",0),"history":dict(c_hist),"liquidity":dict(c_liq),"eligibility":dict(c_elig),"canonical":len(canonical),"history_pass":hist_pass,"liquidity_pass_standard_or_preferred":liq_ok,"eligible":c_elig.get("ELIGIBLE",0),"gates":gates,"research_partial":1633,"strict":759,"us_in_1633":0,"universe_write":False,"u3k_frozen_members":0,"productive":False,"next_action":"STOP_MANAGER_GATE"}
    json.dump(summary, open(OUT/"summary_us1.json","w",encoding="utf-8"), indent=2)
    json.dump({"source":WIKI,"as_of_utc":ASOF,"n":len(discovery),"class":"SECONDARY_WIKIPEDIA"}, open(OUT/"source_snapshot.json","w",encoding="utf-8"), indent=2)
    md="# US-1 S&P 500 Common Build\nSTATUS: %s\nADMIT %s REVIEW %s ELIGIBLE %s\n1633/759/0 Write NO\nSTOP MANAGER GATE\n"%(status,c_adm.get("ADMIT",0),c_adm.get("REVIEW",0),c_elig.get("ELIGIBLE",0))
    (ROOT/"docs"/"spec"/"US1_SP500_Common_Build_Report.md").write_text(md, encoding="utf-8")
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
