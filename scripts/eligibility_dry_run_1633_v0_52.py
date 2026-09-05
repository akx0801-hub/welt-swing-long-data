#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UNI=ROOT/"universe"/"research_partial_1633.csv"
FROZEN=ROOT/"universe"/"SWING_U3K_FROZEN_v0.5.csv"
H38=ROOT/"output_current_master_research_partial_1633_data_refresh_v0_38"/"history_gate_current_1633_v0.38.csv"
L38=ROOT/"output_current_master_research_partial_1633_data_refresh_v0_38"/"liquidity_current_1633_v0.38.csv"
H47=ROOT/"output_history_download_applied_239_v0_47"/"history_qa_239_v0.47.csv"
L48=ROOT/"output_liquidity_fx_sidecar_236_v0_48"/"liquidity_236_v0.48.csv"
C50=ROOT/"output_research_candidates_147_v0_50"/"research_candidates_147_v0.50.csv"
OUT=ROOT/"output_eligibility_dry_run_1633_v0_52"
ORDINARY={"ORDINARY_SHARE","COMMON_STOCK"}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fnum(x):
    try: return None if x in (None,"") else float(x)
    except ValueError: return None
def main():
    if sum(1 for _ in open(FROZEN, encoding="utf-8"))!=1: raise SystemExit("frozen")
    uni_sha=sha(UNI)
    uni=list(csv.DictReader(open(UNI, encoding="utf-8-sig")))
    if len(uni)!=1633: raise SystemExit("universe")
    ident=[{k:r[k] for k in ("WS_ID","ISIN","Primary_MIC","Primary_Ticker") if k in r} for r in uni]
    h38={r["WS_ID"]:r for r in csv.DictReader(open(H38, encoding="utf-8-sig"))}
    l38={r["WS_ID"]:r for r in csv.DictReader(open(L38, encoding="utf-8-sig"))}
    h47={r["WS_ID"]:r for r in csv.DictReader(open(H47, encoding="utf-8"))}
    l48={r["WS_ID"]:r for r in csv.DictReader(open(L48, encoding="utf-8"))}
    c50={r["WS_ID"] for r in csv.DictReader(open(C50, encoding="utf-8"))}
    if len(h47)!=239 or len(l48)!=236: raise SystemExit("sidecar")
    rows=[]
    for r in uni:
        ws=r["WS_ID"]; inst=r.get("Instrument_Type") or ""; mapping=r.get("Mapping_Status") or ""
        if ws in h47:
            hq=h47[ws]; hist_src="v0.47"
            hist="PASS_HISTORY_CURRENT" if hq.get("History_QA")=="PASS_HISTORY" else "INSUFFICIENT_HISTORY"
            bars,valid,yahoo=hq.get("Unique_Bars") or "", hq.get("Valid_Bars") or "", hq.get("Yahoo_Symbol") or r.get("Yahoo_Symbol") or ""
        else:
            ho=h38[ws]; hist_src="v0.38"; st=ho.get("History_Current_State") or ""
            hist={"PASS_HISTORY_CURRENT":"PASS_HISTORY_CURRENT","INSUFFICIENT_HISTORY_FOR_STANDARD_U3K":"INSUFFICIENT_HISTORY","HISTORY_DATA_QUALITY_FAIL":"DATA_QUALITY_FAIL","NOT_REQUESTED_INSTRUMENT_FAIL":"NOT_VERIFIED"}.get(st, st or "UNKNOWN_HISTORY")
            bars,valid,yahoo=ho.get("Unique_Daily_Bars") or "", ho.get("Valid_Completed_Bars") or "", ho.get("Yahoo_Symbol") or r.get("Yahoo_Symbol") or ""
        if ws in l48:
            lq=l48[ws]; liq_src="v0.48"; usable=int(lq.get("Usable20") or 0); med=fnum(lq.get("MedianTurnover20_EUR")); scale=lq.get("Scale") or ""; lclass=lq.get("Liquidity_Class") or "INSUFFICIENT"
        else:
            lo=l38[ws]; liq_src="v0.38"; usable=int(float(lo.get("Usable_Sessions20") or 0)); med=fnum(lo.get("MedianTurnover20_EUR")); scale=lo.get("Quote_Scale_To_Major_Currency") or ""
            st=lo.get("Liquidity_Current_State") or ""
            lclass={"PASS_PREFERRED":"PREFERRED","PASS_STANDARD":"STANDARD","LOW_LIQUIDITY_EXCEPTION_POOL":"LOW_EXCEPTION","FAIL_LIQUIDITY":"FAIL_LIQ"}.get(st,"INSUFFICIENT")
        if mapping=="NOT_VERIFIED" or hist=="NOT_VERIFIED": elig="NOT_VERIFIED"
        elif hist=="INSUFFICIENT_HISTORY": elig="INSUFFICIENT_HISTORY"
        elif hist=="DATA_QUALITY_FAIL": elig="DATA_QUALITY_FAIL"
        elif hist!="PASS_HISTORY_CURRENT": elig="INSUFFICIENT_HISTORY"
        elif inst=="PREFERRED_SHARE": elig="PREFERRED"
        elif inst not in ORDINARY: elig="INSTRUMENT_REVIEW"
        elif lclass in ("FAIL_LIQ","INSUFFICIENT"): elig="FAIL_LIQUIDITY"
        elif lclass=="LOW_EXCEPTION": elig="LOW_LIQUIDITY_EXCEPTION"
        elif lclass in ("PREFERRED","STANDARD"): elig="PASS_STRICT_CANDIDATE"
        else: elig="INSTRUMENT_REVIEW"
        if inst=="UNKNOWN" and elig=="PASS_STRICT_CANDIDATE": elig="INSTRUMENT_REVIEW"
        rows.append({"WS_ID":ws,"Yahoo_Symbol":yahoo,"Name":r.get("Name",""),"Primary_MIC":r.get("Primary_MIC",""),"Mapping_Status":mapping,"Instrument_Type":inst,"Share_Class":r.get("Share_Class",""),"History_State":hist,"History_Source":hist_src,"Unique_Bars":bars,"Valid_Bars":valid,"Liquidity_Class":lclass,"Liquidity_Source":liq_src,"Usable20":usable,"MedianTurnover20_EUR":"" if med is None else round(med,2),"Quote_Scale":scale,"Eligibility_DryRun":elig,"In_v0_50_147":"YES" if ws in c50 else "NO","Universe_Write":"NO"})
    if [{k:r[k] for k in ("WS_ID","ISIN","Primary_MIC","Primary_Ticker") if k in r} for r in uni]!=ident or sha(UNI)!=uni_sha: raise SystemExit("universe mutated")
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT/"eligibility_dry_run_1633_v0.52.csv","w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    elig_c=Counter(x["Eligibility_DryRun"] for x in rows)
    new_strict={x["WS_ID"] for x in rows if x["Eligibility_DryRun"]=="PASS_STRICT_CANDIDATE"}
    by={x["WS_ID"]:x for x in rows}
    only_old=sorted(c50-new_strict)
    summary={"stage":"CURRENT_MASTER_RESEARCH_PARTIAL_1633_ELIGIBILITY_DRY_RUN","version":"v0.52","run_mode":"ELIGIBILITY_DRY_RUN_ONLY","rows":len(rows),"history_counts":dict(Counter(x["History_State"] for x in rows)),"eligibility_counts":dict(elig_c),"pass_strict_candidate":elig_c.get("PASS_STRICT_CANDIDATE",0),"v0_50_147":147,"strict_overlap_with_147":len(new_strict & c50),"strict_not_in_147":len(new_strict-c50),"in_147_not_strict_now":len(only_old),"drop_from_147_reason":dict(Counter(by[ws]["Eligibility_DryRun"] for ws in only_old)),"unknown_blocked_from_strict":sum(1 for x in rows if x["Instrument_Type"]=="UNKNOWN"),"universe_write":False,"u3k_frozen_members":0,"productive":False,"as_of_utc":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    json.dump(summary, open(OUT/"summary_v0.52.json","w",encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2)); return 0
if __name__=="__main__":
    raise SystemExit(main())
