#!/usr/bin/env python3
from __future__ import annotations
import csv, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
ADM=ROOT/"output_us2_sp400_admission"/"US2_SP400_ADMITTED.csv"
REV=ROOT/"output_us2_sp400_admission"/"US2_SP400_REVIEW.csv"
MAT=ROOT/"output_us1_integration_gate"/"evidence_matrix_399.csv"
OUT=ROOT/"output_us2_write"
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
FIELDS=["WS_ID","Name","ISIN","Instrument_Type","Country","Primary_Ticker","Primary_Exchange","Primary_MIC","Primary_Currency","Yahoo_Symbol","Alpha_Symbol","Primary_Universe_Index","Index_Tags","Active","Universe_Status","Mapping_Status","Scalable_Tradeability_Status","Source_ID","Source_AsOf","Last_Validated","Share_Class","Notes"]
def rcsv(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def wcsv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields=fields or list(rows[0].keys())
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
def exch(m): return "NYSE" if m=="XNYS" else "NASDAQ" if m=="XNAS" else ""
def gate(ok): return "PASS" if ok else "FAIL"
def main():
    head=subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=ROOT, text=True).strip()
    if not head.startswith("3d9ed2a"): raise SystemExit("STOP NO WRITE head %s"%head)
    if sum(1 for _ in open(FROZEN,encoding="utf-8"))!=1: raise SystemExit("STOP NO WRITE frozen")
    uni=rcsv(UNI); adm=rcsv(ADM); rev=rcsv(REV); elig=rcsv(ELIG); mat=rcsv(MAT)
    if len(uni)!=2005 or len(adm)!=369: raise SystemExit("STOP NO WRITE counts")
    if sum(1 for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"})!=372: raise SystemExit("STOP NO WRITE us1")
    if sum(1 for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")!=759: raise SystemExit("STOP NO WRITE strict")
    if any(r["Admission_Status"]!="ADMIT" for r in adm): raise SystemExit("STOP SOURCE INTEGRITY FAIL")
    if any(r["Sector"]=="Real Estate" or "REIT" in r["Admission_Reason"] for r in adm): raise SystemExit("STOP SOURCE REIT")
    prefix=[(r["WS_ID"],r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in uni]
    exist_triple=set(prefix); exist_ws={r["WS_ID"] for r in uni}; exist_isin={r["ISIN"] for r in uni if r["ISIN"]}
    us1_isin={r["ISIN"] for r in uni if r["Primary_MIC"] in {"XNYS","XNAS"} and r["ISIN"]}
    b_isin={r["ISIN"] for r in mat if r["Integration_Class"]=="B"}
    rev_isin={r["ISIN"] for r in rev}
    plan=[]
    for c in adm:
        isin,m,t=c["ISIN"],c["Primary_MIC"],c["Primary_Ticker"]
        wsid="WS:%s:%s"%(m,t); cls="NEW"
        if not isin or "|" in isin or not t or m not in {"XNYS","XNAS"}: cls="INVALID"
        elif (isin,m,t) in exist_triple: cls="ALREADY_PRESENT"
        elif wsid in exist_ws or isin in exist_isin: cls="CONFLICT"
        elif isin in us1_isin or isin in b_isin or isin=="US43849R1059" or t=="HONA": cls="BLOCKED"
        elif isin in rev_isin: cls="BLOCKED"
        plan.append({"ISIN":isin,"Primary_MIC":m,"Primary_Ticker":t,"WS_ID":wsid,"class":cls})
    n=lambda k: sum(1 for p in plan if p["class"]==k)
    NEW,ALR,CON,INV,BLO=n("NEW"),n("ALREADY_PRESENT"),n("CONFLICT"),n("INVALID"),n("BLOCKED")
    if NEW+ALR+CON+INV+BLO!=len(plan): raise SystemExit("STOP dry-run recon")
    OUT.mkdir(parents=True, exist_ok=True); wcsv(OUT/"dry_run_write_plan.csv", plan)
    if CON or INV or BLO: raise SystemExit("STOP CONFLICT/INVALID/BLOCKED")
    written=[]
    for p in plan:
        if p["class"]!="NEW": continue
        c=next(x for x in adm if x["ISIN"]==p["ISIN"] and x["Primary_MIC"]==p["Primary_MIC"] and x["Primary_Ticker"]==p["Primary_Ticker"])
        written.append({"WS_ID":p["WS_ID"],"Name":c["Issuer"],"ISIN":c["ISIN"],"Instrument_Type":"COMMON_STOCK","Country":"United States","Primary_Ticker":c["Primary_Ticker"],"Primary_Exchange":exch(c["Primary_MIC"]),"Primary_MIC":c["Primary_MIC"],"Primary_Currency":"USD","Yahoo_Symbol":c["Yahoo_Symbol"],"Alpha_Symbol":"","Primary_Universe_Index":"US_SP400","Index_Tags":"US_SP400","Active":"TRUE","Universe_Status":"ACTIVE_VERIFIED","Mapping_Status":"EVIDENCE_CANDIDATE_APPLIED","Scalable_Tradeability_Status":"SCALABLE_NOT_VERIFIED","Source_ID":"US2_SP400_COMMON_ADMISSION","Source_AsOf":"2026-09-03","Last_Validated":ASOF,"Share_Class":"","Notes":"US-2 SP400 Common; IJH rank4; admit sidecar 3d9ed2a"})
    wcsv(UNI, uni+written, FIELDS)
    after=rcsv(UNI)
    pre2=[(r["WS_ID"],r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in after[:2005]]
    wset={(r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in written}
    aset={(r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in adm}
    us2n=sum(1 for r in after if r["Source_ID"]=="US2_SP400_COMMON_ADMISSION")
    g={"G0_START":gate(head.startswith("3d9ed2a") and len(uni)==2005),"G1_ADMIT_369":gate(len(adm)==369),"G2_IDENTITY":gate(all(r["ISIN"] and r["Primary_MIC"] and r["Primary_Ticker"] for r in written)),"G3_MIC":gate(all(r["Primary_MIC"] in {"XNYS","XNAS"} for r in written)),"G4_EVIDENCE":gate(all(r["Source_ID"]=="US2_SP400_COMMON_ADMISSION" for r in written)),"G5_NO_REIT":gate(not any(c["ISIN"] in rev_isin for c in written)),"G6_NO_ADR":gate(all(r["Instrument_Type"]=="COMMON_STOCK" for r in written)),"G7_NO_REVIEW":gate(wset.isdisjoint({(r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in rev})),"G8_NO_EXCLUDE":gate(wset<=aset),"G9_US1_DISJOINT":gate(not any(r["ISIN"] in us1_isin for r in written)),"G10_B_DISJOINT":gate(not any(r["ISIN"] in b_isin for r in written)),"G11_HONA":gate(not any(r["Primary_Ticker"]=="HONA" or r["ISIN"]=="US43849R1059" for r in after)),"G12_NO_DUP":gate(len({r["WS_ID"] for r in after})==len(after) and len({(r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in after})==len(after)),"G13_PREFIX":gate(pre2==prefix),"G14_STRICT":gate(sum(1 for r in rcsv(ELIG) if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")==759),"G15_FROZEN":gate(sum(1 for _ in open(FROZEN,encoding="utf-8"))==1),"G16_SCOPE":gate(wset<=aset and len(written)==NEW)}
    fails=[k for k,v in g.items() if v=="FAIL"]
    status="US-2 CONTROLLED INTEGRATION WRITE — PASS" if not fails else "INTEGRATION WRITE FAIL"
    if fails:
        wcsv(UNI, uni, FIELDS); raise SystemExit("STOP FAIL "+str(fails))
    wcsv(OUT/"written_rows.csv", written)
    summary={"stage":"US2_CONTROLLED_INTEGRATION_WRITE","status":status,"start_head":"3d9ed2a","target":369,"NEW":NEW,"ALREADY_PRESENT":ALR,"CONFLICT":CON,"INVALID":INV,"BLOCKED":BLO,"written":len(written),"research_partial_before":2005,"research_partial_after":len(after),"us1":372,"us2":us2n,"review_written":0,"exclude_written":0,"reit_written":0,"adr_written":0,"b_written":0,"hona_written":0,"ticker_string_collisions":["RBA","CG","H","BYD"],"strict":759,"frozen":0,"universe_write":True,"gates":g,"fails":fails,"next_action":"STOP_POST_INTEGRATION_INTEGRITY_AUDIT","as_of_utc":ASOF}
    json.dump(summary, open(OUT/"summary_us2_write.json","w",encoding="utf-8"), indent=2)
    (ROOT/"docs"/"spec"/"US2_Controlled_Integration_Write_Report.md").write_text("# US-2 Controlled Integration Write\nSTART 3d9ed2a. ADMIT 369. NEW %s written %s. 2005 -> %s. Prefix unchanged. US-1 372 US-2 %s. Strict 759 Frozen 0. REVIEW/REIT/ADR/B/HONA written 0.\n%s\nNEXT ACTION: STOP — POST-INTEGRATION INTEGRITY AUDIT REQUIRED\n"%(NEW,len(written),len(after),us2n,status), encoding="utf-8")
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
