#!/usr/bin/env python3
"""v0.37 offline reconciliation and refresh planning; intentionally no network clients."""
from __future__ import annotations
import argparse, csv, json, subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output_current_master_research_partial_1633_baseline_v0_37"
BR_FILES=["universe/segments/br_ibrx100_eligibility_state_v0.34.csv","universe/segments/br_ibrx100_standard_eligibility_ready_v0.34.csv","output_current_master_br_ibrx100_eligibility_plan_v0_33/br_ibrx100_standard_eligibility_v0.33.csv","output_current_master_br_ibrx100_eligibility_plan_v0_33/br_ibrx100_history_gate_v0.33.csv","output_current_master_br_ibrx100_liquidity_v0_32/br_ibrx100_liquidity_precheck_v0.32.csv"]
SEGMENTS=("EU_STOXX600","CA_TSX","JP_N225","HK_HSI","CN_CSI300","IN_NIFTY50","TW_TW50","BR_IBRX100")
EXPECTED={"EU_STOXX600":600,"CA_TSX":217,"JP_N225":225,"HK_HSI":93,"CN_CSI300":300,"IN_NIFTY50":50,"TW_TW50":50,"BR_IBRX100":98}

def git(*args): return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
def blob(path):
    try: return git("rev-parse","HEAD:"+path)
    except subprocess.CalledProcessError: return ""
def rows(path):
    p=ROOT/path
    if not p.exists(): return []
    with p.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))
def key(r,*names):
    low={str(k).lower():v for k,v in r.items()}
    for n in names:
        v=low.get(n.lower())
        if str(v or "").strip(): return str(v).strip()
    return ""
def segment(r):
    t=" ".join(str(v or "") for v in r.values()).upper()
    for token,s in [("STOXX","EU_STOXX600"),("TSX","CA_TSX"),("NIKKEI","JP_N225"),("N225","JP_N225"),("HANG SENG","HK_HSI"),("HSI","HK_HSI"),("CSI300","CN_CSI300"),("NIFTY","IN_NIFTY50"),("TW50","TW_TW50"),("TAIWAN 50","TW_TW50"),("IBRX","BR_IBRX100")]:
        if token in t: return s
    return key(r,"Primary_Universe_Index","Universe_Master","Segment_ID")
def write(name,fields,data):
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/name).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
def count_rows(name,col,data):
    c=Counter(str(r.get(col,"")) for r in data)
    write(name,[col,"Rows"],[{col:k,"Rows":v} for k,v in sorted(c.items())])
def br_evidence():
    d=defaultdict(list)
    for p in BR_FILES:
        for r in rows(p):
            w=key(r,"WS_ID","ws_id")
            if w: d[w].append(" ".join(str(v or "") for v in r.values()).upper())
    return d
def br_state(items):
    t=" ".join(items)
    if "STANDARD_ELIGIBILITY_READY" in t:return ("STANDARD_ELIGIBILITY_READY","PASS_HISTORY_PRIOR_EVIDENCE","PASS_STANDARD_PRIOR_EVIDENCE","PASS")
    if "LOW_LIQUIDITY_EXCEPTION" in t:return ("LOW_LIQUIDITY_EXCEPTION_POOL","HISTORY_NOT_CHECKED","LOW_LIQUIDITY_EXCEPTION_POOL_PRIOR","PASS")
    if "NOT_ELIGIBLE_LIQUIDITY" in t:return ("STANDARD_U3K_NOT_ELIGIBLE_LIQUIDITY","HISTORY_NOT_CHECKED","FAIL_LIQUIDITY_PRIOR","PASS")
    if "NOT_ELIGIBLE_INSTRUMENT" in t or "INSTRUMENT_FAIL" in t:return ("STANDARD_U3K_NOT_ELIGIBLE_INSTRUMENT","HISTORY_NOT_CHECKED","LIQUIDITY_NOT_CHECKED","FAIL")
    return ("NOT_ELIGIBLE_OR_NOT_RECONCILED","HISTORY_NOT_CHECKED","LIQUIDITY_NOT_CHECKED","NOT_VERIFIED")
def action(mapping,inst,hist,liq):
    if inst=="FAIL": return "NO_STANDARD_REFRESH_INSTRUMENT_FAIL"
    if mapping in ("MAPPING_MISSING","MAPPING_PENDING"): return "MAPPING_CREATION_REQUIRED"
    if mapping in ("MAPPING_CONFLICT","MAPPING_NOT_VERIFIED"): return "MAPPING_REVALIDATION_REQUIRED"
    if hist=="HISTORY_NOT_CHECKED" and liq=="LIQUIDITY_NOT_CHECKED": return "PRICE_HISTORY_AND_LIQUIDITY_REFRESH_REQUIRED"
    if hist=="HISTORY_NOT_CHECKED": return "PRICE_HISTORY_REFRESH_REQUIRED"
    if liq=="LIQUIDITY_NOT_CHECKED": return "LIQUIDITY_REFRESH_REQUIRED"
    return "ELIGIBILITY_RECOMPUTE_AFTER_REFRESH"
def self_test():
    assert action("MAPPING_PRESENT_NOT_REVALIDATED","FAIL","PASS_HISTORY_PRIOR_EVIDENCE","PASS_STANDARD_PRIOR_EVIDENCE")=="NO_STANDARD_REFRESH_INSTRUMENT_FAIL"
    assert key({"WS_ID":"A"},"WS_ID")=="A" and not key({"Name":"A"},"WS_ID")
    assert action("MAPPING_NOT_VERIFIED","PASS","PASS_HISTORY_PRIOR_EVIDENCE","PASS_STANDARD_PRIOR_EVIDENCE")=="MAPPING_REVALIDATION_REQUIRED"
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--self-test",action="store_true");a=ap.parse_args()
    if a.self_test:self_test();print("self-test PASS");return
    master=rows("universe/research_partial_1633.csv")
    assert len(master)==1633 and len({key(r,"WS_ID","ws_id") for r in master})==1633
    br=br_evidence();ledger=[];exceptions=[]
    for r in master:
        ws=key(r,"WS_ID","ws_id");seg=segment(r);y=key(r,"Yahoo_Symbol","Provider_Symbol","Primary_Ticker")
        mapping="MAPPING_PRESENT_NOT_REVALIDATED" if y else "MAPPING_MISSING"
        prior,hist,liq,inst=("NOT_ELIGIBLE_OR_NOT_RECONCILED","HISTORY_NOT_CHECKED","LIQUIDITY_NOT_CHECKED","NOT_VERIFIED")
        source="CURRENT_CANONICAL"
        if seg=="BR_IBRX100": prior,hist,liq,inst=br_state(br.get(ws,[]));source="CURRENT_SEGMENT_EVIDENCE"
        act=action(mapping,inst,hist,liq)
        ledger.append({"WS_ID":ws,"Name":key(r,"Name","Security_Name"),"ISIN":key(r,"ISIN"),"Country":key(r,"Country"),"Primary_Ticker":key(r,"Primary_Ticker","Ticker"),"Primary_Exchange":key(r,"Primary_Exchange","Exchange"),"Primary_MIC":key(r,"Primary_MIC","MIC"),"Primary_Currency":key(r,"Primary_Currency","Currency"),"Primary_Universe_Index":seg,"Instrument_Type":key(r,"Instrument_Type"),"Universe_Status":key(r,"Universe_Status"),"Source_ID":key(r,"Source_ID"),"Source_AsOf":key(r,"Source_AsOf"),"Mapping_Status_Current":key(r,"Mapping_Status"),"Yahoo_Symbol_Current":y,"Mapping_Baseline_State":mapping,"Scalable_Tradeability_Status":key(r,"Scalable_Tradeability_Status") or "SCALABLE_NOT_VERIFIED","Identity_Baseline_State":"NOT_VERIFIED","Instrument_Gate_Baseline_State":inst,"History_Evidence_State":hist,"History_Evidence_AsOf":"","History_First_Date":"","History_Last_Completed_Date":"","History_Unique_Daily_Bars":"","History_Valid_Completed_Bars":"","Liquidity_Evidence_State":liq,"Liquidity_Evidence_AsOf":"","MedianTurnover20_EUR":"","Liquidity_Class_Prior":"","Prior_Eligibility_State":prior,"Eligibility_Baseline_State":"PRIOR_EVIDENCE_REQUIRES_REFRESH","Price_Derived_Data_Refresh_Required":"true","Mapping_Refresh_Required":str(mapping!="MAPPING_PRESENT_NOT_REVALIDATED").lower(),"Identity_Instrument_Remediation_Required":str(inst=="FAIL").lower(),"Planned_Next_Action":act,"Refresh_Priority":"P0_BLOCKED" if inst=="FAIL" else "P1","Evidence_Source":source,"Evidence_Confidence":"MEDIUM" if seg=="BR_IBRX100" else "LOW","Productive_Eligibility":"false","SWING_U3K_FROZEN_Member":"false"})
    assert len(ledger)==1633 and len({x["WS_ID"] for x in ledger})==1633 and Counter(x["Primary_Universe_Index"] for x in ledger)==Counter(EXPECTED)
    fields=list(ledger[0]);write("eligibility_baseline_1633_v0.37.csv",fields,ledger)
    refresh=[{"WS_ID":x["WS_ID"],"Primary_Universe_Index":x["Primary_Universe_Index"],"Primary_MIC":x["Primary_MIC"],"Primary_Ticker":x["Primary_Ticker"],"Instrument_Gate_State":x["Instrument_Gate_Baseline_State"],"Mapping_Baseline_State":x["Mapping_Baseline_State"],"History_Evidence_State":x["History_Evidence_State"],"Liquidity_Evidence_State":x["Liquidity_Evidence_State"],"Scalable_Tradeability_Status":x["Scalable_Tradeability_Status"],"Refresh_Required":"true","Refresh_Priority":x["Refresh_Priority"],"Refresh_Action":x["Planned_Next_Action"],"Refresh_Prerequisite":"NONE","Planned_Provider":"TO_BE_CONTROLLED","Provider_Symbol_Current":x["Yahoo_Symbol_Current"],"Network_Required_In_Execution_Stage":"true","Expected_Output":"CURRENT_ELIGIBILITY_INPUT","Reason":"v0.37 offline prior evidence"} for x in ledger]
    write("data_refresh_plan_1633_v0.37.csv",list(refresh[0]),refresh)
    for name,col in [("identity_baseline_counts_v0.37.csv","Identity_Baseline_State"),("instrument_baseline_counts_v0.37.csv","Instrument_Gate_Baseline_State"),("mapping_baseline_counts_v0.37.csv","Mapping_Baseline_State"),("history_baseline_counts_v0.37.csv","History_Evidence_State"),("liquidity_baseline_counts_v0.37.csv","Liquidity_Evidence_State"),("scalable_baseline_counts_v0.37.csv","Scalable_Tradeability_Status"),("prior_eligibility_counts_v0.37.csv","Prior_Eligibility_State")]: count_rows(name,col,ledger)
    count_rows("refresh_action_counts_v0.37.csv","Planned_Next_Action",ledger)
    inv=[{"Artifact_Path":p,"Artifact_Blob_SHA":blob(p),"Stage_or_Version":"v0.34/v0.33/v0.32","Evidence_Type":"Brazil prior evidence","Universe_Lineage":"CURRENT_SEGMENT_EVIDENCE","Rows":len(rows(p)),"AsOf_or_PriceAsOf":"","Authority_Class":"CURRENT_SEGMENT_EVIDENCE","Usable_For_Current_Baseline":"true","Reason":"prior evidence only"} for p in BR_FILES]
    write("historical_eligibility_evidence_inventory_v0.37.csv",list(inv[0]),inv)
    write("baseline_evidence_lineage_v0.37.csv",["Evidence_ID","Artifact_Path","Blob_SHA","Stage","Evidence_Type","Authority_Class","Rows_Used","Join_Key","AsOf","Notes"],[{"Evidence_ID":"CURRENT_MASTER","Artifact_Path":"universe/research_partial_1633.csv","Blob_SHA":blob("universe/research_partial_1633.csv"),"Stage":"v0.36","Evidence_Type":"canonical membership","Authority_Class":"CURRENT_CANONICAL","Rows_Used":1633,"Join_Key":"WS_ID","AsOf":"","Notes":"offline"}])
    write("baseline_reconciliation_exceptions_v0.37.csv",["Exception_Type","WS_ID","Details"],exceptions)
    write("data_refresh_batch_plan_v0.37.csv",["Batch_ID","Segment_ID","Primary_MIC_or_Group","Action","Rows","Prerequisite","Provider","Estimated_Request_Mode","Fail_Closed_Rule","Execution_Order"],[{"Batch_ID":"B1","Segment_ID":"ALL","Primary_MIC_or_Group":"BATCH","Action":"CONTROLLED_REFRESH","Rows":1633,"Prerequisite":"mapping","Provider":"TO_BE_CONTROLLED","Estimated_Request_Mode":"batch-cache","Fail_Closed_Rule":"no eligibility promotion","Execution_Order":1}])
    write("eligibility_recompute_plan_v0.37.csv",["Step","Action","State"],[{"Step":1,"Action":"Identity/Instrument, mapping, history, liquidity, data quality, eligibility recompute","State":"PLANNING_ONLY"}])
    counts={k:dict(Counter(x[k] for x in ledger)) for k in ["Identity_Baseline_State","Instrument_Gate_Baseline_State","Mapping_Baseline_State","History_Evidence_State","Liquidity_Evidence_State","Scalable_Tradeability_Status","Prior_Eligibility_State","Planned_Next_Action"]}
    summary={"stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_ELIGIBILITY_BASELINE_RECONCILIATION_AND_DATA_REFRESH_PLAN","version":"v0.37","current_master_rows":1633,"baseline_ledger_rows":1633,"refresh_plan_rows":1633,"data_refresh_executed_v0_37":False,"baseline_reconciled_v0_37":True,"data_refresh_plan_materialized_v0_37":True,"universe_mutated_v0_37":False,"eligibility_promotion_v0_37":False,"productive":False,"p0":False,"swing_u3k_frozen":False,"next_stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_MAPPING_HISTORY_LIQUIDITY_DATA_REFRESH","counts":counts}
    (OUT/"summary_v0.37.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    (OUT/"stage_checkpoint_v0.37.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    (OUT/"manifest_v0.37.json").write_text(json.dumps({"outputs":sorted(p.name for p in OUT.iterdir())},indent=2),encoding="utf-8")
    print("v0.37 PASS")
if __name__=="__main__": main()
