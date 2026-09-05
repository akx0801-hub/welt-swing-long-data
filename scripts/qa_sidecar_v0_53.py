#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, re, sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
H38=ROOT/"output_current_master_research_partial_1633_data_refresh_v0_38"/"history_gate_current_1633_v0.38.csv"
H47=ROOT/"output_history_download_applied_239_v0_47"/"history_qa_239_v0.47.csv"
OUT=ROOT/"output_qa_v0_53"
AS_OF=date(2026,9,5)
SQLS=[ROOT/"runtime_cache"/"applied_239_history_v0_47.sqlite", ROOT/"runtime_cache"/"price_cache.sqlite"]
IDENTITY=("WS_ID","ISIN","Primary_MIC","Primary_Ticker")
ORDINARY={"ORDINARY_SHARE","COMMON_STOCK"}
LEGAL=re.compile(r"\b(SA|NV|AG|SE|PLC|LTD|LIMITED|INC|CORP|CO|GROUP|THE|S A|N V)\b")
TAIL=re.compile(r"\b(PREF\.?|PREFERRED|VORZUG|PN|ON|UNIT|UNT|ED|NM|N1|N2|ATZ|EJ|EDJ|PNA)\b")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gi(x):
    try: return int(float(x or 0))
    except ValueError: return 0
def ikey(n):
    n=re.sub(r"\s+"," ",(n or "").upper()); n=TAIL.sub(" ",n); n=LEGAL.sub(" ",n)
    return re.sub(r"\s+"," ",re.sub(r"[^A-Z0-9 ]"," ",n)).strip()
def map_sc(raw):
    s=(raw or "").strip()
    if not s: return "not available"
    u=s.upper()
    if "NOT_VERIFIED" in u or "NOT VERIFIED" in u: return "not verified"
    if u in {"VERIFIED","SCALABLE_VERIFIED","TRADEABLE"}: return "verified"
    if "CACHED" in u or "PLAUSIBLE" in u: return "cached/plausible"
    return "not verified"
def canonical(g):
    ords=[r for r in g if r["Instrument_Type"] in ORDINARY]
    prefs=[r for r in g if r["Instrument_Type"]=="PREFERRED_SHARE"]
    units=[r for r in g if r["Instrument_Type"]=="UNIT"]
    if len({r["Primary_MIC"] for r in g})>1 and ords and not prefs:
        return "","DUAL_LISTING_MULTI_MIC","Kein Merge ueber MIC."
    if ords:
        c=sorted(ords, key=lambda r: float(r.get("MedianTurnover20_EUR") or 0), reverse=True)[0]
        return c["WS_ID"],"ORDINARY_LIKE","Ordinary/Common vor Preferred; sonst hoehere MedianTurnover20_EUR."
    if prefs: return "","NO_ORDINARY_IN_UNIVERSE","Nur Preferred in 1633."
    if units: return "","UNIT_REVIEW","Unit ist REVIEW."
    return "","REVIEW","Keine Ordinary-Like-Klasse."
def sqlite_stats():
    path=next((p for p in SQLS if p.exists()), None)
    if not path: return None, {}
    con=sqlite3.connect(str(path)); cols=[r[1] for r in con.execute("PRAGMA table_info(price_daily)")]
    if not {"ws_id","day"}.issubset(set(cols)): con.close(); return str(path), {}
    out={}
    for ws,n,nuniq,dmin,dmax in con.execute("SELECT ws_id, COUNT(*), COUNT(DISTINCT day), MIN(day), MAX(day) FROM price_daily GROUP BY ws_id"):
        out[ws]={"n":n,"nuniq":nuniq,"min":dmin or "","max":dmax or ""}
    con.close(); return str(path), out
def frozen_ok():
    if sum(1 for _ in open(FROZEN, encoding="utf-8"))!=1: raise SystemExit("frozen")
def main():
    frozen_ok(); uni_sha=sha(UNI)
    uni=list(csv.DictReader(open(UNI, encoding="utf-8-sig")))
    elig=list(csv.DictReader(open(ELIG, encoding="utf-8")))
    if len(uni)!=1633 or len(elig)!=1633: raise SystemExit("rowcount")
    ident=[{k:r[k] for k in IDENTITY if k in r} for r in uni]
    by={r["WS_ID"]:r for r in elig}
    h38={r["WS_ID"]:r for r in csv.DictReader(open(H38, encoding="utf-8-sig"))}
    h47={r["WS_ID"]:r for r in csv.DictReader(open(H47, encoding="utf-8"))}
    sql_path, sql=sqlite_stats(); sidecar=[]; bar=[]; future_n=dup_n=0; bst=Counter()
    for r in uni:
        e=by[r["WS_ID"]]; raw=r.get("Scalable_Tradeability_Status") or ""; sc=map_sc(raw)
        unique=gi(e.get("Unique_Bars")); valid=gi(e.get("Valid_Bars"))
        ho=h38.get(r["WS_ID"], {}); hq=h47.get(r["WS_ID"], {})
        last=hq.get("Last_Bar") or ho.get("Last_Completed_Bar") or ""; first=hq.get("First_Bar") or ho.get("First_Valid_Bar") or ""
        future=bool(last and last>AS_OF.isoformat()); sr=sql.get(r["WS_ID"]); dup=False; dsrc="CSV_UNIQUE_ONLY"
        if sr:
            dup=sr["n"]!=sr["nuniq"]; unique,valid=sr["nuniq"],sr["nuniq"]; last=sr["max"] or last; first=sr["min"] or first; dsrc="SQLITE"
        if future: future_n+=1
        if dup: dup_n+=1
        flags=[]
        if unique<260: flags.append("LT_260")
        if valid<252: flags.append("LT_252")
        if future: flags.append("FUTURE")
        if dup: flags.append("DUPS")
        st="NO_BARS" if unique==0 else ("FAIL_"+"+".join(flags) if flags else "PASS_BAR_QA"); bst[st]+=1
        row=dict(e); row.update({"Scalable_Universe_Raw":raw,"Scalable_QA":sc,"Scalable_Live_Check":"NO","Bar_Unique":unique,"Bar_Valid":valid,"Bar_First":first,"Bar_Last":last,"Bar_Future":"YES" if future else "NO","Bar_Dups":"YES" if dup else "NO","Bar_Dup_Source":dsrc,"Bar_QA_Status":st,"Eligibility_DryRun_Unchanged":e["Eligibility_DryRun"],"Universe_Write":"NO"})
        sidecar.append(row)
        bar.append({"WS_ID":r["WS_ID"],"Yahoo_Symbol":e.get("Yahoo_Symbol",""),"History_State":e.get("History_State",""),"History_Source":e.get("History_Source",""),"Unique_Bars":unique,"Valid_Bars":valid,"First_Bar":first,"Last_Bar":last,"Future":"YES" if future else "NO","Duplicates":"YES" if dup else "NO","Dup_Source":dsrc,"Pass_260":"YES" if unique>=260 else "NO","Pass_252":"YES" if valid>=252 else "NO","Bar_QA_Status":st,"Eligibility_DryRun":e["Eligibility_DryRun"],"Sqlite_Used":"YES" if sr else "NO"})
    groups=defaultdict(list)
    for r in uni:
        e=by[r["WS_ID"]]
        groups[ikey(r["Name"])].append({"WS_ID":r["WS_ID"],"Name":r["Name"],"ISIN":r["ISIN"],"Primary_MIC":r["Primary_MIC"],"Primary_Ticker":r["Primary_Ticker"],"Instrument_Type":r["Instrument_Type"],"Share_Class":r.get("Share_Class") or "","Liquidity_Class":e.get("Liquidity_Class",""),"MedianTurnover20_EUR":e.get("MedianTurnover20_EUR",""),"Eligibility_DryRun":e.get("Eligibility_DryRun","")})
    report=[]; nkeys=0
    for k,g in groups.items():
        types={x["Instrument_Type"] for x in g}; share=" ".join(x["Share_Class"].lower() for x in g)
        if not (len(g)>1 or bool(types & {"PREFERRED_SHARE","UNIT"}) or any(t in share for t in ("c share","sdb","participation","depositary","pref")) or "PREF" in " ".join(x["Name"].upper() for x in g)):
            continue
        nkeys+=1; can,gtype,why=canonical(g)
        for x in g:
            report.append({**x,"Issuer_Key":k,"Group_Size":len(g),"Group_Type":gtype,"Group_Tickers":"|".join(sorted(y["Primary_Ticker"] for y in g)),"Canonical_Scan_WS_ID":can,"Is_Canonical_Scan_Class":"YES" if x["WS_ID"]==can and can else "NO","Canonical_Reason":why,"Universe_Write":"NO"})
    OUT.mkdir(parents=True, exist_ok=True)
    def wcsv(path, rows):
        with open(path,"w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    wcsv(OUT/"multi_share_class_v0.53.csv", report)
    wcsv(OUT/"eligibility_sidecar_scalable_v0.53.csv", sidecar)
    wcsv(OUT/"history_bar_qa_1633_v0.53.csv", bar)
    if [{k:r[k] for k in IDENTITY if k in r} for r in uni]!=ident or sha(UNI)!=uni_sha: raise SystemExit("universe mutated")
    frozen_ok()
    elig_c=Counter(r["Eligibility_DryRun"] for r in sidecar); strict=elig_c.get("PASS_STRICT_CANDIDATE",0)
    sc_c=Counter(r["Scalable_QA"] for r in sidecar)
    summary={"stage":"QA_SIDECAR_V0_53","version":"v0.53","run_mode":"QA_DOCS_ONLY","rows":1633,"multi_share_class_groups":nkeys,"multi_share_class_rows":len(report),"group_type_counts":dict(Counter(r["Group_Type"] for r in report)),"canonical_yes":sum(1 for r in report if r["Is_Canonical_Scan_Class"]=="YES"),"scalable_qa_counts":dict(sc_c),"bar_qa_counts":dict(bst),"history_future_dates":future_n,"history_duplicates":dup_n,"sqlite_path":sql_path,"sqlite_ws_ids":len(sql),"pass_strict_candidate":strict,"pass_strict_unchanged_from_v0_52":strict==759,"v0_52_strict":759,"strict_bar_lt_260":sum(1 for r in sidecar if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE" and gi(r["Bar_Unique"])<260),"universe_write":False,"eligibility_promoted":False,"u3k_frozen_members":0,"productive":False,"as_of":AS_OF.isoformat(),"as_of_utc":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    json.dump(summary, open(OUT/"summary_v0.53.json","w",encoding="utf-8"), indent=2)
    md=ROOT/"docs"/"validation"/"v0.53_QA_Report.md"; md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text("# v0.53 QA Report\n\nHEAD d093ec1. Universe_Write=NO. Strict %s (unchanged=%s). Frozen=0.\n\nA groups %s / rows %s / types %s\n\nB Scalable_QA %s — kein Live-Check.\n\nC Bar QA %s; future=%s; dups=%s; sqlite=%s.\n\nKeine Eligibility-Aenderung. Stopp nach v0.53.\n"%(strict, strict==759, nkeys, len(report), summary["group_type_counts"], dict(sc_c), dict(bst), future_n, dup_n, sql_path or "ABSENT"), encoding="utf-8")
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
