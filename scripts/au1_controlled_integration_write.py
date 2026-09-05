#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
ELIG=ROOT/"output_eligibility_dry_run_1633_v0_52"/"eligibility_dry_run_1633_v0.52.csv"
SEAL=ROOT/"output_au1_evidence_gate"/"AU1_INTEGRATION_READY.csv"
REV=ROOT/"output_au1_admission_build"/"AU1_ADMISSION_REVIEW.csv"
EXC=ROOT/"output_au1_admission_build"/"AU1_ADMISSION_EXCLUDE.csv"
OUT=ROOT/"output_au1_write"
SEAL_SHA="2921df416aeb33ddf4e224ff89792ff9789f6f429a845841750454997ae7d21f"
FORBIDDEN={"PDIDB","SGH","VAU","DNL","ELV","NWS"}
EXPECTED_TARGET=153; EXPECTED_NEW=153
EXPECTED_ALREADY_PRESENT=0; EXPECTED_CONFLICT=0; EXPECTED_INVALID=0; EXPECTED_BLOCKED=0
WRITE_ALLOWED=False
FIELDS=["WS_ID","Name","ISIN","Instrument_Type","Country","Primary_Ticker","Primary_Exchange","Primary_MIC","Primary_Currency","Yahoo_Symbol","Alpha_Symbol","Primary_Universe_Index","Index_Tags","Active","Universe_Status","Mapping_Status","Scalable_Tradeability_Status","Source_ID","Source_AsOf","Last_Validated","Share_Class","Notes"]
ASOF=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def rcsv(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def wcsv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields=fields or list(rows[0].keys())
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
def gate(ok): return "PASS" if ok else "FAIL"
def main():
    global WRITE_ALLOWED
    head=subprocess.check_output(["git","rev-parse","--short","HEAD"], cwd=ROOT, text=True).strip()
    if sum(1 for _ in open(FROZEN,encoding="utf-8"))!=1: raise SystemExit("STOP — START STATE MISMATCH frozen")
    uni=rcsv(UNI); elig=rcsv(ELIG)
    if len(uni)!=2374: raise SystemExit("STOP — START STATE MISMATCH n=%s"%len(uni))
    if sum(1 for r in uni if r.get("Primary_MIC")=="XASX")!=0: raise SystemExit("STOP — START STATE MISMATCH AU")
    if sum(1 for r in uni if r["Source_ID"]=="US1_SP500_COMMON_EVIDENCE_GATE")!=372: raise SystemExit("STOP — START STATE MISMATCH us1")
    if sum(1 for r in uni if r["Source_ID"]=="US2_SP400_COMMON_ADMISSION")!=369: raise SystemExit("STOP — START STATE MISMATCH us2")
    if sum(1 for r in elig if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")!=759: raise SystemExit("STOP — START STATE MISMATCH strict")
    if not SEAL.exists(): raise SystemExit("STOP — SEALED INPUT INVALID missing")
    raw=SEAL.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    if sha!=SEAL_SHA: raise SystemExit("STOP — SEALED INPUT INVALID sha %s"%sha)
    src=rcsv(SEAL)
    if len(src)!=153: raise SystemExit("STOP — SEALED INPUT INVALID n=%s"%len(src))
    if any(r.get("Final_Admission_Status")!="INTEGRATION_READY" for r in src): raise SystemExit("STOP — SEALED INPUT INVALID status")
    if any(not r.get("ISIN") or not r.get("MIC") or not r.get("Primary_Ticker") for r in src): raise SystemExit("STOP — SEALED INPUT INVALID identity")
    if any(r.get("MIC")!="XASX" for r in src): raise SystemExit("STOP — SEALED INPUT INVALID mic")
    if len({(r["ISIN"],r["MIC"],r["Primary_Ticker"]) for r in src})!=153: raise SystemExit("STOP — SEALED INPUT INVALID dup")
    ticks={r["Primary_Ticker"] for r in src}
    if ticks & FORBIDDEN: raise SystemExit("STOP — SEALED INPUT INVALID forbidden %s"%(ticks&FORBIDDEN))
    rev_t={r["Primary_Ticker"] for r in rcsv(REV)}; exc_t={r.get("Primary_Ticker") for r in rcsv(EXC) if r.get("Primary_Ticker")}
    if ticks & rev_t or ticks & exc_t: raise SystemExit("STOP — SEALED INPUT INVALID review/exclude")
    prefix=[(r["WS_ID"],r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in uni]
    exist_triple=set(prefix); exist_ws={r["WS_ID"] for r in uni}
    exist_isin={r["ISIN"] for r in uni if r["ISIN"]}
    exist_isin_mic={(r["ISIN"],r["Primary_MIC"]) for r in uni if r["ISIN"]}
    exist_mic_t={(r["Primary_MIC"],r["Primary_Ticker"]) for r in uni}
    plan=[]
    for c in src:
        isin,m,t=c["ISIN"],c["MIC"],c["Primary_Ticker"]
        wsid=c["WS_ID"] or "WS:%s:%s"%(m,t); cls="NEW"
        if t in FORBIDDEN or t in rev_t or t in exc_t: cls="BLOCKED"
        elif not isin or not t or m!="XASX" or not isin.startswith("AU"): cls="INVALID"
        elif (isin,m,t) in exist_triple: cls="ALREADY_PRESENT"
        elif wsid in exist_ws or isin in exist_isin or (isin,m) in exist_isin_mic or (m,t) in exist_mic_t: cls="CONFLICT"
        plan.append({"ISIN":isin,"Primary_MIC":m,"Primary_Ticker":t,"WS_ID":wsid,"class":cls})
    n=lambda k: sum(1 for p in plan if p["class"]==k)
    NEW,ALR,CON,INV,BLO=n("NEW"),n("ALREADY_PRESENT"),n("CONFLICT"),n("INVALID"),n("BLOCKED")
    OUT.mkdir(parents=True, exist_ok=True); wcsv(OUT/"dry_run_write_plan.csv", plan)
    dry={"TARGET":len(plan),"NEW":NEW,"ALREADY_PRESENT":ALR,"CONFLICT":CON,"INVALID":INV,"BLOCKED":BLO,"WRITE_ALLOWED":False}
    json.dump(dry, open(OUT/"dry_run_summary.json","w",encoding="utf-8"), indent=2)
    print("DRY-RUN", json.dumps(dry))
    if not (len(plan)==EXPECTED_TARGET and NEW==EXPECTED_NEW and ALR==EXPECTED_ALREADY_PRESENT and CON==EXPECTED_CONFLICT and INV==EXPECTED_INVALID and BLO==EXPECTED_BLOCKED):
        raise SystemExit("STOP — DRY-RUN NOT WRITE-ELIGIBLE NEW=%s ALR=%s CON=%s INV=%s BLO=%s"%(NEW,ALR,CON,INV,BLO))
    WRITE_ALLOWED=True
    written=[]
    for p in plan:
        c=next(x for x in src if x["ISIN"]==p["ISIN"])
        t=c["Primary_Ticker"]
        written.append({"WS_ID":p["WS_ID"],"Name":c["Issuer"],"ISIN":c["ISIN"],"Instrument_Type":"COMMON_STOCK","Country":"Australia","Primary_Ticker":t,"Primary_Exchange":"ASX","Primary_MIC":"XASX","Primary_Currency":"AUD","Yahoo_Symbol":"%s.AX"%t,"Alpha_Symbol":"","Primary_Universe_Index":"AU_SP_ASX200","Index_Tags":"AU_SP_ASX200","Active":"TRUE","Universe_Status":"ACTIVE_VERIFIED","Mapping_Status":"EVIDENCE_CANDIDATE_APPLIED","Scalable_Tradeability_Status":"SCALABLE_NOT_VERIFIED","Source_ID":"AU1_EVIDENCE_ADMISSION_GATE","Source_AsOf":"2026-09-03","Last_Validated":ASOF,"Share_Class":"","Notes":"AU-1 S&P/ASX 200 Ordinary; local sealed INTEGRATION_READY sha256 2921df416aeb33dd; Evidence Gate; not origin sidecar"})
    wcsv(UNI, uni+written, FIELDS)
    after=rcsv(UNI)
    pre2=[(r["WS_ID"],r["ISIN"],r["Primary_MIC"],r["Primary_Ticker"]) for r in after[:2374]]
    wt={r["Primary_Ticker"] for r in written}
    au=sum(1 for r in after if r["Primary_MIC"]=="XASX")
    nonempty_isin=[r["ISIN"] for r in after if r["ISIN"]]
    g={
        "G0":gate(len(uni)==2374),
        "G1":gate(len(src)==153),
        "G2":gate(sha==SEAL_SHA),
        "G3":gate(wt.isdisjoint(FORBIDDEN) and not (wt & rev_t) and not (wt & exc_t)),
        "G4":gate(all(r["ISIN"] and r["Primary_MIC"] and r["Primary_Ticker"] and r["WS_ID"] for r in written)),
        "G5":gate(all(r["Primary_MIC"]=="XASX" for r in written)),
        "G6":gate(len(plan)==153),
        "G7":gate(NEW==153),
        "G8":gate(ALR==0),
        "G9":gate(CON==0),
        "G10":gate(INV==0),
        "G11":gate(BLO==0),
        "G12":gate(pre2==prefix),
        "G13":gate(len(written)==153),
        "G14":gate(len(after)==2527),
        "G15":gate(au==153),
        "G16":gate(sum(1 for r in rcsv(ELIG) if r["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE")==759 and sum(1 for _ in open(FROZEN,encoding="utf-8"))==1),
        "G17":gate(sum(1 for r in after if r["Source_ID"]=="US1_SP500_COMMON_EVIDENCE_GATE")==372 and sum(1 for r in after if r["Source_ID"]=="US2_SP400_COMMON_ADMISSION")==369 and len({r["WS_ID"] for r in after})==len(after) and len(nonempty_isin)==len(set(nonempty_isin))),
    }
    fails=[k for k,v in g.items() if v=="FAIL"]
    status="AU-1 CONTROLLED INTEGRATION WRITE — PASS" if not fails and WRITE_ALLOWED else "AU-1 CONTROLLED INTEGRATION WRITE — FAIL"
    if fails:
        wcsv(UNI, uni, FIELDS); raise SystemExit("STOP FAIL "+str(fails))
    wcsv(OUT/"written_rows.csv", written, FIELDS)
    summary={"stage":"AU1_CONTROLLED_INTEGRATION_WRITE","status":status,"start_head":head,"sealed_input":str(SEAL.relative_to(ROOT)),"sealed_sha256":sha,"input_count":153,"WRITE_ALLOWED":WRITE_ALLOWED,"target":153,"NEW":NEW,"ALREADY_PRESENT":ALR,"CONFLICT":CON,"INVALID":INV,"BLOCKED":BLO,"written":len(written),"research_partial_before":2374,"research_partial_after":len(after),"au_before":0,"au_after":au,"us1":372,"us2":369,"strict":759,"frozen":0,"universe_write":True,"gates":g,"fails":fails,"next_action":"STOP_POST_INTEGRATION_INTEGRITY_AUDIT","as_of_utc":ASOF}
    json.dump(summary, open(OUT/"summary_au1_write.json","w",encoding="utf-8"), indent=2)
    md="\n".join([
        "# AU-1 Controlled Integration Write Report",
        "Start HEAD: %s"%head,
        "Local sealed input: output_au1_evidence_gate/AU1_INTEGRATION_READY.csv (not on origin; not reconstructed from 159).",
        "Input SHA256: %s"%sha,
        "Input Count = 153. All Final_Admission_Status=INTEGRATION_READY.",
        "Dry-run: TARGET 153 NEW %s ALREADY_PRESENT %s CONFLICT %s INVALID %s BLOCKED %s."%(NEW,ALR,CON,INV,BLO),
        "WRITE_ALLOWED default False. Lifted only because AND-guard matched 153/153/0/0/0/0.",
        "Written = %s. Provenance Source_ID=AU1_EVIDENCE_ADMISSION_GATE + local sealed source sha256 2921df416aeb33dd. No origin sidecar path claimed."%len(written),
        "Research Partial 2374 -> %s. AU 0 -> %s."%(len(after), au),
        "Prefix-Integrity: first 2374 identity tuples FIELD DIFF = 0 (G12).",
        "Duplicate QA: unique WS_ID; nonempty ISIN unique; full identity unique. Ticker-only vs other MIC allowed.",
        "Exclusion QA: PDIDB/SGH/VAU/DNL/ELV/NWS NOT WRITTEN. Build REVIEW/EXCLUDE NOT WRITTEN.",
        "No-touch: Strict 759 Frozen 0 US-1 372 US-2 369 v7.2 untouched.",
        "Gates G0-G17: %s"%g,
        "Commit: write script + write artifacts + research partial + this report only. Evidence-gate sidecar not in this commit.",
        "Next: SEPARATE AU-1 Post-Integration Integrity Audit. WRITE PASS ≠ AUDIT PASS.",
        "Status: "+status,
    ])
    (ROOT/"docs"/"spec"/"AU1_Controlled_Integration_Write_Report.md").write_text(md+"\n", encoding="utf-8")
    print(json.dumps({k:summary[k] for k in summary if k!="gates"}, indent=2)); print(json.dumps(g, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
