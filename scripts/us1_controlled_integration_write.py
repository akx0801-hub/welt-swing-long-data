#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
CAND=ROOT/"output_us1_integration_gate"/"US1_INTEGRATION_CANDIDATES.csv"
MAT=ROOT/"output_us1_integration_gate"/"evidence_matrix_399.csv"
OUT=ROOT/"output_us1_write"
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
FIELDS=["WS_ID","Name","ISIN","Instrument_Type","Country","Primary_Ticker","Primary_Exchange","Primary_MIC","Primary_Currency","Yahoo_Symbol","Alpha_Symbol","Primary_Universe_Index","Index_Tags","Active","Universe_Status","Mapping_Status","Scalable_Tradeability_Status","Source_ID","Source_AsOf","Last_Validated","Share_Class","Notes"]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rcsv(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def wcsv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields=fields or list(rows[0].keys())
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
def exch(mic): return "NYSE" if mic=="XNYS" else "NASDAQ" if mic=="XNAS" else ""
def main():
    if sum(1 for _ in open(FROZEN,encoding="utf-8"))!=1: raise SystemExit("STOP frozen")
    uni_sha=sha(UNI)
    uni=rcsv(UNI); elig=rcsv(ELIG); cands=rcsv(CAND); mat=rcsv(MAT)
    if len(uni)!=1633: raise SystemExit("STOP uni %s"%len(uni))
    if sum(1 for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"})!=0: raise SystemExit("STOP us already")
    if sum(1 for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")!=759: raise SystemExit("STOP strict")
    if len(cands)!=372: raise SystemExit("STOP candidates %s"%len(cands))
    ident0=[(r["WS_ID"],r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in uni]
    u_isin={r["ISIN"] for r in uni if r["ISIN"]}
    u_triple={(r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in uni}
    u_ws={r["WS_ID"] for r in uni}
    b_tick={r["Ticker"] for r in mat if r["Integration_Class"]=="B"}
    e_tick={r["Ticker"] for r in mat if r["Integration_Class"]=="E"}
    plan=[]
    for c in cands:
        reason="NEW"
        if c["Primary_Ticker"] in b_tick or c["Yahoo_Symbol"]=="HONA" or c["Primary_Ticker"] in e_tick:
            reason="BLOCKED_SCOPE"
        elif c["Primary_MIC"] not in {"XNYS","XNAS"} or "|" in c["ISIN"] or not c["ISIN"].startswith("US"):
            reason="INVALID"
        elif not c["Primary_Ticker"] or (c["ISIN"],c["Primary_MIC"],c["Primary_Ticker"]) in u_triple:
            reason="ALREADY_PRESENT"
        elif c["ISIN"] in u_isin:
            reason="CONFLICT"
        elif ("WS:%s:%s"%(c["Primary_MIC"],c["Primary_Ticker"])) in u_ws:
            reason="CONFLICT"
        plan.append({**c, "DryRun":reason, "New_WS_ID":"WS:%s:%s"%(c["Primary_MIC"],c["Primary_Ticker"])})
    from collections import Counter
    pc=Counter(r["DryRun"] for r in plan)
    OUT.mkdir(parents=True, exist_ok=True)
    wcsv(OUT/"dry_run_write_plan.csv", plan)
    new=[r for r in plan if r["DryRun"]=="NEW"]
    blocked=[r for r in plan if r["DryRun"]!="NEW"]
    if pc.get("CONFLICT") or pc.get("INVALID") or pc.get("BLOCKED_SCOPE"):
        json.dump({"status":"STOP_NO_WRITE","plan":dict(pc)}, open(OUT/"summary_us1_write.json","w"), indent=2)
        print(json.dumps({"status":"STOP_NO_WRITE","plan":dict(pc)}, indent=2)); return 1
    rows=[]
    for c in new:
        rows.append({"WS_ID":c["New_WS_ID"],"Name":c["Issuer"],"ISIN":c["ISIN"],"Instrument_Type":"COMMON_STOCK","Country":"United States","Primary_Ticker":c["Primary_Ticker"],"Primary_Exchange":exch(c["Primary_MIC"]),"Primary_MIC":c["Primary_MIC"],"Primary_Currency":"USD","Yahoo_Symbol":c["Yahoo_Symbol"],"Alpha_Symbol":"","Primary_Universe_Index":"US_SP500","Index_Tags":"US_SP500","Active":"TRUE","Universe_Status":"ACTIVE_VERIFIED","Mapping_Status":"YFINANCE_VERIFIED","Scalable_Tradeability_Status":"SCALABLE_NOT_VERIFIED","Source_ID":"US1_SP500_COMMON_EVIDENCE_GATE","Source_AsOf":"2026-09-03","Last_Validated":ASOF,"Share_Class":"","Notes":"US-1 S&P500 Common class A; IVV+Wikipedia; cand=%s"%c["WS_ID"]})
    if any(t in b_tick for t in (c["Primary_Ticker"] for c in new)): raise SystemExit("B leaked")
    if any(c["Yahoo_Symbol"]=="HONA" for c in new): raise SystemExit("HONA leaked")
    wcsv(UNI, uni+rows, FIELDS)
    after=rcsv(UNI)
    if len(after)!=1633+len(rows): raise SystemExit("post count")
    if sum(1 for r in after if r["Primary_MIC"] in {"XNYS","XNAS"})!=len(rows): raise SystemExit("us count")
    if sum(1 for _ in open(FROZEN,encoding="utf-8"))!=1: raise SystemExit("frozen")
    if sum(1 for r in rcsv(ELIG) if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")!=759: raise SystemExit("strict mutated")
    if [(r["WS_ID"],r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in after[:1633]]!=ident0: raise SystemExit("old mutated")
    status="INTEGRATION_WRITE_PASS" if not blocked else "INTEGRATION_WRITE_PARTIAL"
    summary={"stage":"US1_CONTROLLED_INTEGRATION_WRITE","status":status,"start_head":"ae35b69","write_source":"output_us1_integration_gate/US1_INTEGRATION_CANDIDATES.csv","target_candidates":372,"dry_run":dict(pc),"new_records":len(new),"already_present":pc.get("ALREADY_PRESENT",0),"blocked":pc.get("BLOCKED_SCOPE",0),"conflicts":pc.get("CONFLICT",0),"invalid":pc.get("INVALID",0),"actual_written":len(rows),"research_partial_before":1633,"research_partial_after":len(after),"us_before":0,"us_after":len(rows),"strict_before":759,"strict_after":759,"frozen_before":0,"frozen_after":0,"duplicates_created":False,"identity_conflicts":False,"evidence_review_written":0,"hona_written":False,"scope_integrity":"PASS","provenance":"US1_SP500_COMMON_EVIDENCE_GATE","pre_sha256":uni_sha,"post_sha256":sha(UNI),"as_of_utc":ASOF,"next_action":"STOP_MANAGER_GATE"}
    json.dump(summary, open(OUT/"summary_us1_write.json","w",encoding="utf-8"), indent=2)
    wcsv(OUT/"written_rows.csv", rows, FIELDS)
    md="# US-1 Controlled Integration Write\nSTART HEAD ae35b69\nSTATUS %s\nTarget 372 NEW %s Written %s\nResearch 1633 -> %s\nUS 0 -> %s\nStrict 759 -> 759 Frozen 0 -> 0\nB written 0 HONA written 0\nSTOP MANAGER GATE\n"%(status,len(new),len(rows),len(after),len(rows))
    (ROOT/"docs"/"spec"/"US1_Controlled_Integration_Write_Report.md").write_text(md, encoding="utf-8")
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
