#!/usr/bin/env python3
"""v0.37 offline reconciliation and refresh planning; intentionally no network clients."""
from __future__ import annotations
import argparse, csv, json, subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output_current_master_research_partial_1633_baseline_v0_37"
RESEARCH = ROOT / "universe/research_partial_1633.csv"
BR_FILES = [
 "universe/segments/br_ibrx100_eligibility_state_v0.34.csv",
 "universe/segments/br_ibrx100_standard_eligibility_ready_v0.34.csv",
 "output_current_master_br_ibrx100_eligibility_plan_v0_33/br_ibrx100_standard_eligibility_v0.33.csv",
 "output_current_master_br_ibrx100_eligibility_plan_v0_33/br_ibrx100_history_gate_v0.33.csv",
 "output_current_master_br_ibrx100_liquidity_v0_32/br_ibrx100_liquidity_precheck_v0.32.csv",
]
SEGMENTS = ("EU_STOXX600","CA_TSX","JP_N225","HK_HSI","CN_CSI300","IN_NIFTY50","TW_TW50","BR_IBRX100")
EXPECTED = {"EU_STOXX600":600,"CA_TSX":217,"JP_N225":225,"HK_HSI":93,"CN_CSI300":300,"IN_NIFTY50":50,"TW_TW50":50,"BR_IBRX100":98}
MISSING = {"US_SP1500","MX_IPC","KR_KOSPI200","AU_ASX200","NZ_NZX50","ZA_TOP40"}

def git(*args):
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def blob(path):
    try: return git("rev-parse","HEAD:"+path)
    except subprocess.CalledProcessError: return ""

def rows(path):
    p=ROOT/path
    if not p.exists(): return []
    with p.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))

def key(row,*names):
    low={str(k).lower():v for k,v in row.items()}
    for n in names:
        if n.lower() in low and str(low[n.lower()] or "").strip(): return str(low[n.lower()]).strip()
    return ""

def segment(row):
    t=" ".join(str(v or "") for v in row.values()).upper()
    tests=[("STOXX","EU_STOXX600"),("TSX","CA_TSX"),("NIKKEI","JP_N225"),("N225","JP_N225"),("HANG SENG","HK_HSI"),("HSI","HK_HSI"),("CSI300","CN_CSI300"),("CSI 300","CN_CSI300"),("NIFTY","IN_NIFTY50"),("TW50","TW_TW50"),("TAIWAN 50","TW_TW50"),("IBRX","BR_IBRX100")]
    for token,s in tests:
        if token in t:return s
    return key(row,"Primary_Universe_Index","Universe_Master","Segment_ID")

def state_text(row):
    return " ".join(str(v or "") for v in row.values()).upper()

def br_evidence():
    out=defaultdict(list)
    for path in BR_FILES:
        for r in rows(path):
            w=key(r,"WS_ID","ws_id")
            if w: out[w].append((path,r,state_text(r)))
    return out

def classify_br(items):
    text=" ".join(x[2] for x in items)
    prior="NOT_ELIGIBLE_OR_NOT_RECONCILED"
    hist="HISTORY_NOT_CHECKED"; liq="LIQUIDITY_NOT_CHECKED"; inst="NOT_VERIFIED"
    if "STANDARD_ELIGIBILITY_READY" in text:
        prior="STANDARD_ELIGIBILITY_READY"; hist="PASS_HISTORY_PRIOR_EVIDENCE"; liq="PASS_STANDARD_PRIOR_EVIDENCE"; inst="PASS"
    elif "LOW_LIQUIDITY_EXCEPTION" in text:
        prior="LOW_LIQUIDITY_EXCEPTION_POOL"; liq="LOW_LIQUIDITY_EXCEPTION_POOL_PRIOR"; inst="PASS"
    elif "NOT_ELIGIBLE_LIQUIDITY" in text:
        prior="STANDARD_U3K_NOT_ELIGIBLE_LIQUIDITY"; liq="FAIL_LIQUIDITY_PRIOR"; inst="PASS"
    elif "NOT_ELIGIBLE_INSTRUMENT" in text or "INSTRUMENT_FAIL" in text:
        prior="STANDARD_U3K_NOT_ELIGIBLE_INSTRUMENT"; inst="FAIL"
    return prior,hist,liq,inst

def action(mapping,inst,hist,liq):
    if inst=="FAIL": return "NO_STANDARD_REFRESH_INSTRUMENT_FAIL"
    if mapping in ("MAPPING_MISSING","MAPPING_PENDING"): return "MAPPING_CREATION_REQUIRED"
    if mapping in ("MAPPING_CONFLICT","MAPPING_NOT_VERIFIED"): return "MAPPING_REVALIDATION_REQUIRED"
    if "QUALITY_FAIL" in hist or "QUALITY_FAIL" in liq:return "DATA_QUALITY_REMEDIATION_REQUIRED"
    if hist in ("HISTORY_NOT_CHECKED","HISTORY_EVIDENCE_STALE_OR_NEEDS_REFRESH") and liq in ("LIQUIDITY_NOT_CHECKED","LIQUIDITY_EVIDENCE_STALE_OR_NEEDS_REFRESH"):return "PRICE_HISTORY_AND_LIQUIDITY_REFRESH_REQUIRED"
    if hist in ("HISTORY_NOT_CHECKED","HISTORY_EVIDENCE_STALE_OR_NEEDS_REFRESH"):return "PRICE_HISTORY_REFRESH_REQUIRED"
    if liq in ("LIQUIDITY_NOT_CHECKED","LIQUIDITY_EVIDENCE_STALE_OR_NEEDS_REFRESH"):return "LIQUIDITY_REFRESH_REQUIRED"
    return "ELIGIBILITY_RECOMPUTE_AFTER_REFRESH"

def write(name,fieldnames,data):
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/name).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames);w.writeheader();w.writerows(data)

def count_rows(name,col,data):
    c=Counter(str(r.get(col,"")) for r in data)
    write(name,[col,"Rows"],[{col:k,"Rows":v} for k,v in sorted(c.items())])

def self_test():
    current={"WS_ID":"A","Yahoo_Symbol":"A"}; legacy={"Name":"A"}
    assert key(current,"WS_ID")=="A" and not key(legacy,"WS_ID")
    assert action("MAPPING_PRESENT_NOT_REVALIDATED","FAIL","PASS_HISTORY_PRIOR_EVIDENCE","PASS_STANDARD_PRIOR_EVIDENCE")=="NO_STANDARD_REFRESH_INSTRUMENT_FAIL"
    assert action("MAPPING_NOT_VERIFIED","PASS","PASS_HISTORY_PRIOR_EVIDENCE","PASS_STANDARD_PRIOR_EVIDENCE")=="MAPPING_REVALIDATION_REQUIRED"

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--self-test",action="store_true");a=ap.parse_args()
    if a.self_test:self_test();print("self-test PASS");return
    master=rows("universe/research_partial_1633.csv")
    if len(master)!=1633: raise SystemExit("research_partial_1633 row gate failed")
    if len({key(r,"WS_ID","ws_id") for r in master})!=1633:raise SystemExit("WS_ID uniqueness gate failed")
    br=br_evidence(); ledger=[]; exceptions=[]
    for r in master:
        ws=key(r,"WS_ID","ws_id"); seg=segment(r)
        if seg not in SEGMENTS: exceptions.append({"Exception_Type":"UNRESOLVED_SEGMENT","WS_ID":ws,"Details":seg})
        yahoo=key(r,"Yahoo_Symbol","Yahoo Symbol","Provider_Symbol","Primary_Ticker")
        mapping="MAPPING_PRESENT_NOT_REVALIDATED" if yahoo else "MAPPING_MISSING"
        prior="NOT_ELIGIBLE_OR_NOT_RECONCILED";hist="HISTORY_NOT_CHECKED";liq="LIQUIDITY_NOT_CHECKED";inst="NOT_VERIFIED";source="CURRENT_CANONICAL"
        if seg=="BR_IBRX100":
            prior,hist,liq,inst=classify_br(br.get(ws,[]));source="CURRENT_SEGMENT_EVIDENCE"
        if hist.startswith("PASS_"):hist="PASS_HISTORY_PRIOR_EVIDENCE"
        if liq in ("PASS_STANDARD_PRIOR_EVIDENCE","PASS_PREFERRED_PRIOR_EVIDENCE","LOW_LIQUIDITY_EXCEPTION_POOL_PRIOR","FAIL_LIQUIDITY_PRIOR"): pass
        else: liq="LIQUIDITY_NOT_CHECKED"
        act=action(mapping,inst,hist,liq)
        ledger.append({
          "WS_ID":ws,"Name":key(r,"Name","Security_Name","Company_Name"),"ISIN":key(r,"ISIN"),"Country":key(r,"Country"),"Primary_Ticker":key(r,"Primary_Ticker","Ticker"),"Primary_Exchange":key(r,"Primary_Exchange","Exchange"),"Primary_MIC":key(r,"Primary_MIC","MIC"),"Primary_Currency":key(r,"Primary_Currency","Currency"),"Primary_Universe_Index":seg,"Instrument_Type":key(r,"Instrument_Type"),"Universe_Status":key(r,"Universe_Status"),"Source_ID":key(r,"Source_ID"),"Source_AsOf":key(r,"Source_AsOf"),
          "Mapping_Status_Current":key(r,"Mapping_Status"),"Yahoo_Symbol_Current":yahoo,"Mapping_Baseline_State":mapping,"Scalable_Tradeability_Status":key(r,"Scalable_Tradeability_Status") or "SCALABLE_NOT_VERIFIED","Identity_Baseline_State":"NOT_VERIFIED","Instrument_Gate_Baseline_State":inst,
          "History_Evidence_State":hist,"History_Evidence_AsOf":"","History_First_Date":"","History_Last_Completed_Date":"","History_Unique_Daily_Bars":"","History_Valid_Completed_Bars":"","Liquidity_Evidence_State":liq,"Liquidity_Evidence_AsOf":"","MedianTurnover20_EUR":"","Liquidity_Class_Prior":"",
          "Prior_Eligibility_State":prior,"Eligibility_Baseline_State":"PRIOR_EVIDENCE_REQUIRES_REFRESH","Price_Derived_Data_Refresh_Required":"true","Mapping_Refresh_Required":str(mapping!="MAPPING_PRESENT_NOT_REVALIDATED").lower(),"Identity_Instrument_Remediation_Required":str(inst=="FAIL").lower(),"Planned_Next_Action":act,"Refresh_Priority":"P1" if inst!="FAIL" else "P0_BLOCKED","Evidence_Source":source,"Evidence_Confidence":"MEDIUM" if seg=="BR_IBRX100" else "LOW","Productive_Eligibility":"false","SWING_U3K_FROZEN_Member":"false"})
    cnt=Counter(r["Primary_Universe_Index"] for r in ledger)
    if cnt!=Counter(EXPECTED):raise SystemExit("segment count gate failed: "+repr(cnt))
    fields=list(ledger[0]);write("eligibility_baseline_1633_v0.37.csv",fields,ledger)
    refresh=[]
    for r in ledger:
        refresh.append({k:r.get(k,"") for k in ["WS_ID","Primary_Universe_Index","Primary_MIC","Primary_Ticker","Instrument_Gate_Baseline_State","Mapping_Baseline_State","History_Evidence_State","Liquidity_Evidence_State","Scalable_Tradeability_Status"]}|{"Refresh_Required":"true","Refresh_Priority":r["Refresh_Priority"],"Refresh_Action":r["Planned_Next_Action"],"Refresh_Prerequisite":"Instrument remediation" if r["Instrument_Gate_Baseline_State"]=="FAIL" else "Mapping verification","Planned_Provider":"UNDECIDED_OFFLINE","Provider_Symbol_Current":r["Yahoo_Symbol_Current"],"Network_Required_In_Execution_Stage":"true","Expected_Output":"revalidated history/liquidity evidence","Reason":"v0.37 is offline; prior price-derived evidence is not current"})
    write("data_refresh_plan_1633_v0.37.csv",list(refresh[0]),refresh)
    batches=Counter((r["Primary_Universe_Index"],r["Primary_MIC"] or "MIC_UNRESOLVED",r["Refresh_Action"]) for r in refresh)
    write("data_refresh_batch_plan_v0.37.csv",["Batch_ID","Segment_ID","Primary_MIC_or_Group","Action","Rows","Prerequisite","Provider","Estimated_Request_Mode","Fail_Closed_Rule","Execution_Order"],[{"Batch_ID":"B%03d"%i,"Segment_ID":k[0],"Primary_MIC_or_Group":k[1],"Action":k[2],"Rows":v,"Prerequisite":"mapping/identity gate","Provider":"UNDECIDED_OFFLINE","Estimated_Request_Mode":"batch/cache","Fail_Closed_Rule":"no current eligibility PASS","Execution_Order":i} for i,(k,v) in enumerate(sorted(batches.items()),1)])
    write("eligibility_recompute_plan_v0.37.csv",["Step","Action","State"],[{"Step":i,"Action":x,"State":"PLANNED_ONLY"} for i,x in enumerate(["Identity/Instrument remediation","Mapping verification/creation","Price history refresh","Liquidity refresh","Data quality gate","Standard eligibility recompute","Scalable plausibility revalidation","Funnel decision"],1)])
    inv=[]
    for p in git("ls-files").splitlines():
        q=p.lower()
        if any(x in q for x in ("mapping","history","liquidity","turnover","eligibility","tradeability","price")):
            inv.append({"Artifact_Path":p,"Artifact_Blob_SHA":blob(p),"Stage_or_Version":p.split("_v")[-1] if "_v" in p else "historical","Evidence_Type":"HISTORICAL_OR_SEGMENT_EVIDENCE","Universe_Lineage":"UNCLASSIFIED_OFFLINE","Rows":"","AsOf_or_PriceAsOf":"","Authority_Class":"CURRENT_SEGMENT_EVIDENCE" if "br_ibrx100" in q else "HISTORICAL_DIAGNOSTIC","Usable_For_Current_Baseline":"true" if "br_ibrx100" in q else "false","Reason":"inventoried offline; only stable WS_ID joins promoted"})
    write("historical_eligibility_evidence_inventory_v0.37.csv",list(inv[0]) if inv else ["Artifact_Path"],inv)
    used=[{"Evidence_ID":"E%03d"%i,"Artifact_Path":p,"Blob_SHA":blob(p),"Stage":"v0.37 predecessor","Evidence_Type":"FROZEN_INPUT","Authority_Class":"CURRENT_CANONICAL","Rows_Used":"","Join_Key":"WS_ID","AsOf":"","Notes":""} for i,p in enumerate(["universe/research_partial_1633.csv"]+BR_FILES,1)]
    write("baseline_evidence_lineage_v0.37.csv",list(used[0]),used)
    write("baseline_reconciliation_exceptions_v0.37.csv",["Exception_Type","WS_ID","Details"],exceptions)
    count_rows("mapping_baseline_counts_v0.37.csv","Mapping_Baseline_State",ledger);count_rows("history_baseline_counts_v0.37.csv","History_Evidence_State",ledger);count_rows("liquidity_baseline_counts_v0.37.csv","Liquidity_Evidence_State",ledger);count_rows("scalable_baseline_counts_v0.37.csv","Scalable_Tradeability_Status",ledger);count_rows("prior_eligibility_counts_v0.37.csv","Prior_Eligibility_State",ledger)
    count_rows("identity_baseline_counts_v0.37.csv","Identity_Baseline_State",ledger)
    count_rows("instrument_baseline_counts_v0.37.csv","Instrument_Gate_Baseline_State",ledger)
    count_rows("refresh_action_counts_v0.37.csv","Planned_Next_Action",ledger)
    summary={"stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_ELIGIBILITY_BASELINE_RECONCILIATION_AND_DATA_REFRESH_PLAN","version":"v0.37","current_master_rows":1633,"baseline_ledger_rows":len(ledger),"data_refresh_executed_v0_37":False,"baseline_reconciled_v0_37":True,"data_refresh_plan_materialized_v0_37":True,"universe_mutated_v0_37":False,"eligibility_promotion_v0_37":False,"productive":False,"p0":False,"swing_u3k_frozen":False,"source_superset_complete":False,"full_scan_allowed":False,"next_stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_BASELINE_COLLISION_REMEDIATION" if exceptions else "CURRENT_MASTER_RESEARCH_PARTIAL_1633_MAPPING_HISTORY_LIQUIDITY_DATA_REFRESH","counts":{"identity":dict(Counter(r["Identity_Baseline_State"] for r in ledger)),"instrument":dict(Counter(r["Instrument_Gate_Baseline_State"] for r in ledger)),"mapping":dict(Counter(r["Mapping_Baseline_State"] for r in ledger)),"history":dict(Counter(r["History_Evidence_State"] for r in ledger)),"liquidity":dict(Counter(r["Liquidity_Evidence_State"] for r in ledger)),"scalable":dict(Counter(r["Scalable_Tradeability_Status"] for r in ledger)),"prior_eligibility":dict(Counter(r["Prior_Eligibility_State"] for r in ledger)),"refresh_action":dict(Counter(r["Planned_Next_Action"] for r in ledger)),"exceptions":len(exceptions)}}
    (OUT/"summary_v0.37.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    (OUT/"stage_checkpoint_v0.37.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    (OUT/"manifest_v0.37.json").write_text(json.dumps({"files":sorted(p.name for p in OUT.iterdir()),"offline":True},indent=2)+"\n",encoding="utf-8")
    handoff="\n".join(["# WELT-SWING CURRENT HANDOFF v0.37","","Current Master = 1633","Operating Mode = RESEARCH_PARTIAL","Imported = 8/14; Missing = 6/14","Baseline Ledger Rows = 1633","Data Refresh Executed = false","P0 = false","SWING_U3K_FROZEN = false","Productive = false","Source Governance v0.36 remains unchanged","Next Stage = "+summary["next_stage"],""])
    (ROOT/"WELT-SWING-CURRENT-Handoff-v0.37.md").write_text(handoff,encoding="utf-8");(ROOT/"WELT-SWING-CURRENT-Handoff-CURRENT.md").write_text(handoff,encoding="utf-8")
if __name__=="__main__":main()
