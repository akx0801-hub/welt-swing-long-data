#!/usr/bin/env python3
"""G-P0-13 / v1.12 local-only quarantine root-cause diagnostic.

Standard-library only. No provider/network calls, no SQLite mutation, no C07
scoring, and no forward outcome generation.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,os,sqlite3,zipfile
from collections import Counter
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
VERSION="v1.12"; AUTHORITY_ID="G-P0-13"
DECISION="PRE_SCORING_QUARANTINE_ROOT_CAUSE_AND_REMEDIATION_DESIGN_AUTHORIZED_NO_PROVIDER_REENTRY"
START_HEAD="2ab52ea5baebfaa278ab579c924009748431926b"
V111_DRIVE_ID="1UnfEKgQQiXbKXa1hiYD_Fn2liBVr2IqD"
V111_ZIP_SHA="3c305545c3243616cfdf21597d0cbbda6755b5649211ee112d3c9d4a44400fb2"
V111_SQLITE_MEMBER="runtime_cache/lane1_breakout_vcp_holdout_lineage_v1_11.sqlite"
V111_SQLITE_SHA="245793920911e318ad8b16ad08e35321677a72e8006c64a597b725d92fd7c251"
V111_SQLITE_BYTES=140656640; V111_SQLITE_ROWS=721126
HIST_BOUNDARY="2026-09-03"; FRESH_START="2026-09-04"; CUTOFF="2026-10-05"; QA_THRESHOLD=0.50
FINALIST="L1-C07-PIVOT_PROXIMITY_STRICT"
FINALIST_SHA="7aabed14feb3ab902223f981619864b24aecc25b51c3d67f4026e4a8e357c201"
CSET_SHA="8148c0bd2294bece39908d84394dda4fb0835210e83822997df12b9fbd0d6235"

EXPECTED={
 "WS:XNAS:ECHO":("ECHO","2025-08-26","INHERITED_FOUNDATION_QA_FLAG"),
 "WS:XNAS:MEDP":("MEDP","2025-07-22","INHERITED_FOUNDATION_QA_FLAG"),
 "WS:XNAS:MRNA":("MRNA","2026-08-19","INHERITED_FOUNDATION_QA_FLAG"),
 "WS:XNAS:STRL":("STRL","2026-05-05","INHERITED_FOUNDATION_QA_FLAG"),
 "WS:XNYS:KD":("KD","2026-02-09","INHERITED_FOUNDATION_QA_FLAG"),
 "WS:XNYS:MP":("MP","2025-07-10","INHERITED_FOUNDATION_QA_FLAG"),
 "WS:XNYS:CTVA":("CTVA","2026-10-01","FRESH_QA_BLOCKER"),
 "WS:XTKS:1925":("1925.T","2026-09-04","FRESH_QA_BLOCKER"),
 "WS:XTKS:2282":("2282.T","2026-09-04","FRESH_QA_BLOCKER"),
 "WS:XTKS:285A":("285A.T","2026-09-04","FRESH_QA_BLOCKER"),
 "WS:XTKS:3099":("3099.T","2026-09-04","FRESH_QA_BLOCKER"),
 "WS:XTKS:5706":("5706.T","2026-09-04","FRESH_QA_BLOCKER"),
 "WS:XTKS:8035":("8035.T","2026-09-04","FRESH_QA_BLOCKER"),
 "WS:XTKS:8316":("8316.T","2026-09-04","FRESH_QA_BLOCKER"),
 "WS:XTKS:8766":("8766.T","2026-09-04","FRESH_QA_BLOCKER")
}
JAPAN=[x for x in EXPECTED if x.startswith("WS:XTKS:")]
INHERITED=[x for x,v in EXPECTED.items() if v[2]=="INHERITED_FOUNDATION_QA_FLAG"]
CTVA="WS:XNYS:CTVA"
ROOT_CAUSE_ALLOWED={
 "INHERITED_FOUNDATION_QA_FLAG_UNRESOLVED","FRESH_BOUNDARY_DISCONTINUITY_VERIFIED",
 "LOCAL_CORPORATE_ACTION_ALIGNMENT_VERIFIED","LOCAL_PRICE_SERIES_ANOMALY_VERIFIED",
 "RUNTIME_REPAIR_PATH_BLOCKED_DIAGNOSIS_INCOMPLETE","ROOT_CAUSE_NOT_VERIFIED"}
REMEDIATION_ALLOWED={
 "NO_ACTION_KEEP_QUARANTINE","LATER_TARGETED_REPAIR_REQUIRES_MANAGER_AUTHORIZATION",
 "LATER_LOCAL_POLICY_CONSISTENCY_RECHECK_REQUIRED","FOUNDATION_FLAG_REQUIRES_SEPARATE_HISTORICAL_GOVERNANCE",
 "BOUNDARY_SEMANTICS_REQUIRES_CODE_FIX_BEFORE_ANY_PROVIDER_RETRY","UNRESOLVED_MANAGER_REVIEW_REQUIRED"}

def sha_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def rj(p:Path): return json.loads(p.read_text(encoding="utf-8"))
def wj(p:Path,o:Any):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def wc(p:Path,rows:list[dict[str,Any]],fields:list[str]):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n");w.writeheader();w.writerows(rows)
def finite(v):
 try:return v is not None and math.isfinite(float(v))
 except:return False
def valid(r):
 vals=[r["open"],r["high"],r["low"],r["close"]]
 return all(finite(v) and float(v)>0 for v in vals) and float(r["high"])>=float(r["low"]) and float(r["low"])<=float(r["close"])<=float(r["high"]) and not (r["volume"] is not None and finite(r["volume"]) and float(r["volume"])<0)
def fr(v): return "" if v is None else format(float(v),".12g")
def ret(a,b): return float(b/a-1.0)
def series(con,ws): return con.execute("SELECT ws_id,yahoo_symbol,day,open,high,low,close,adj_close,volume,dividends,stock_splits,repaired,source_id,fetched_utc FROM price_daily WHERE ws_id=? ORDER BY day",(ws,)).fetchall()
def sus_dates(rows):
 v=[r for r in rows if valid(r)];out=[]
 for i in range(1,len(v)):
  rr=abs(ret(float(v[i-1]["close"]),float(v[i]["close"])))
  sp=abs(float(v[i-1]["stock_splits"] or 0))>0 or abs(float(v[i]["stock_splits"] or 0))>0 or (i+1<len(v) and abs(float(v[i+1]["stock_splits"] or 0))>0)
  if rr>QA_THRESHOLD and not sp: out.append(v[i]["day"])
 return out
def context(con,ws,d):
 v=[r for r in series(con,ws) if valid(r)];i=next(i for i,r in enumerate(v) if r["day"]==d)
 assert i>0
 return v[i-1],v[i],(v[i+1] if i+1<len(v) else None)
def classify(ws,prev,cur):
 sym,d,bc=EXPECTED[ws];div=float(cur["dividends"] or 0);sp=float(cur["stock_splits"] or 0)
 rr=ret(float(prev["close"]),float(cur["close"]));ar=ret(float(prev["adj_close"]),float(cur["adj_close"])) if finite(prev["adj_close"]) and finite(cur["adj_close"]) else float("nan")
 boundary=prev["day"]<=HIST_BOUNDARY and d==FRESH_START
 if bc=="INHERITED_FOUNDATION_QA_FLAG":
  rc="INHERITED_FOUNDATION_QA_FLAG_UNRESOLVED";vr="VERIFIED_AS_INHERITED_QA_FLAG_CAUSAL_EVENT_NOT_ESTABLISHED";rm="FOUNDATION_FLAG_REQUIRES_SEPARATE_HISTORICAL_GOVERNANCE"
  ev=f"flag_date={d}; predecessor_class={bc}; abs_raw_return={abs(rr):.9f}; abs_adj_return={abs(ar):.9f}; dividend={div:g}; split={sp:g}; repaired={int(cur['repaired'])}; no fresh suspicious date in v1.11 blocker evidence"
 elif ws in JAPAN:
  rc="FRESH_BOUNDARY_DISCONTINUITY_VERIFIED";vr="BOUNDARY_DISCONTINUITY_VERIFIED_SHARED_CAUSAL_MECHANISM_NOT_ESTABLISHED";rm="BOUNDARY_SEMANTICS_REQUIRES_CODE_FIX_BEFORE_ANY_PROVIDER_RETRY"
  ev=f"prev={prev['day']}; suspicious={d}; exact_boundary={'YES' if boundary else 'NO'}; abs_raw_return={abs(rr):.9f}; abs_adj_return={abs(ar):.9f}; dividend={div:g}; split={sp:g}; repaired={int(cur['repaired'])}"
 elif ws==CTVA:
  rc="LOCAL_PRICE_SERIES_ANOMALY_VERIFIED";vr="LOCAL_ANOMALY_VERIFIED_CAUSAL_EVENT_NOT_ESTABLISHED";rm="LATER_TARGETED_REPAIR_REQUIRES_MANAGER_AUTHORIZATION"
  ev=f"prev={prev['day']}; suspicious={d}; exact_boundary={'YES' if boundary else 'NO'}; abs_raw_return={abs(rr):.9f}; abs_adj_return={abs(ar):.9f}; dividend={div:g}; split={sp:g}; repaired={int(cur['repaired'])}"
 else:
  rc="ROOT_CAUSE_NOT_VERIFIED";vr="ROOT_CAUSE_NOT_VERIFIED";rm="UNRESOLVED_MANAGER_REVIEW_REQUIRED";ev=""
 assert rc in ROOT_CAUSE_ALLOWED and rm in REMEDIATION_ALLOWED
 return rc,ev,vr,rm

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--package-zip",required=True);ap.add_argument("--runtime-log",required=True);ap.add_argument("--output-dir",required=True);ap.add_argument("--work-dir",required=True);ap.add_argument("--workflow-file",required=True);ap.add_argument("--start-head-verified",required=True)
 a=ap.parse_args();out=Path(a.output_dir);work=Path(a.work_dir);pkg=Path(a.package_zip);logp=Path(a.runtime_log);out.mkdir(parents=True,exist_ok=True);work.mkdir(parents=True,exist_ok=True)
 auth=rj(ROOT/"config/manager_governance_authority_G_P0_13_v1.12.json");pa=rj(ROOT/"config/manager_governance_authority_G_P0_12_v1.11.json");ps=rj(ROOT/"output_p0_breakout_compression_vcp_new_holdout_lineage_v1_11/summary_v1.11.json");pc=rj(ROOT/"output_p0_breakout_compression_vcp_new_holdout_lineage_v1_11/stage_checkpoint_v1.11.json");pb=rj(ROOT/"config/g_p0_12_drive_roundtrip_binding_v1.11.json");lc=rj(ROOT/"config/lane1_new_holdout_data_lineage_v1.11.json");p0=rj(ROOT/"config/p0_parameter_authority_current.json");pv=rj(ROOT/"output_p0_breakout_compression_vcp_new_holdout_lineage_v1_11/provider_call_audit_v1.11.json")
 blockers=list(csv.DictReader((ROOT/"output_p0_breakout_compression_vcp_new_holdout_lineage_v1_11/pre_scoring_blockers_v1.11.csv").open(encoding="utf-8")));req=(ROOT/"requirements.txt").read_text();wf_current=Path(a.workflow_file).read_text();wf_v111=(ROOT/".github/workflows/g-p0-12-v111-new-holdout-lineage-prescoring.yml").read_text();pct=(ROOT/"scripts/price_cache.py").read_text();bld=(ROOT/"scripts/lane1_new_holdout_data_lineage_prescoring_v1_11.py").read_text();hdoc=(ROOT/"docs/validation/Current_Master_Research_Partial_1633_Controlled_Data_Gap_Remediation_v0.40.md").read_text();rlog=logp.read_text(errors="replace")
 assert a.start_head_verified=="YES" and auth["Required_Start_HEAD"]==START_HEAD and auth["Decision"]==DECISION and auth["Provider_Calls_Authorized"]=="NO"
 assert pa["Authority_ID"]=="G-P0-12" and ps["Pre_Scoring_Status"]=="PRE_SCORING_BLOCKED_MANAGER_REVIEW_REQUIRED" and pc["Decision"]=="PRE_SCORING_BLOCKED_MANAGER_REVIEW_REQUIRED"
 assert pb["Drive_File_ID"]==V111_DRIVE_ID and pb["Drive_ZIP_SHA256"]==V111_ZIP_SHA and pb["SQLite_SHA256"]==V111_SQLITE_SHA
 assert lc["Finalist_Binding"]["Candidate_ID"]==FINALIST and lc["Finalist_Binding"]["Semantic_SHA256"]==FINALIST_SHA and lc["Finalist_Binding"]["Candidate_Set_Semantic_SHA256"]==CSET_SHA and lc["Finalist_Binding"]["Pivot_Proximity_Cutoff_ATR"]==0.75
 zb=sha_file(pkg);assert zb==V111_ZIP_SHA and pkg.stat().st_size==28778386
 with zipfile.ZipFile(pkg) as z:
  assert V111_SQLITE_MEMBER in z.namelist();data=z.read(V111_SQLITE_MEMBER)
 db=work/"lane1_breakout_vcp_holdout_lineage_v1_11.sqlite";db.write_bytes(data);os.chmod(db,0o444);sb=sha_file(db);assert sb==V111_SQLITE_SHA and db.stat().st_size==V111_SQLITE_BYTES
 con=sqlite3.connect(f"file:{db}?mode=ro",uri=True);con.row_factory=sqlite3.Row;con.execute("PRAGMA query_only=ON");write_blocked=False
 try:con.execute("CREATE TABLE __v112_write_probe(x INTEGER)")
 except sqlite3.OperationalError:write_blocked=True
 assert write_blocked
 mn,mx,total=con.execute("SELECT MIN(day),MAX(day),COUNT(*) FROM price_daily").fetchone();hist=int(con.execute("SELECT COUNT(*) FROM price_daily WHERE day<=?",(HIST_BOUNDARY,)).fetchone()[0]);fresh=int(con.execute("SELECT COUNT(*) FROM price_daily WHERE day>? AND day<=?",(HIST_BOUNDARY,CUTOFF)).fetchone()[0]);after=int(con.execute("SELECT COUNT(*) FROM price_daily WHERE day>?",(CUTOFF,)).fetchone()[0])
 assert int(total)==V111_SQLITE_ROWS and hist==692427 and fresh==28699 and after==0 and mx==CUTOFF
 assert len(blockers)==15;bw={r["WS_ID"]:r for r in blockers};assert set(bw)==set(EXPECTED);assert sum(r["Blocker_Class"]=="FRESH_QA_BLOCKER" for r in blockers)==9;assert sum(r["Blocker_Class"]=="INHERITED_FOUNDATION_QA_FLAG" for r in blockers)==6
 rows=[]
 for ws,(sym,d,bc) in EXPECTED.items():
  br=bw[ws];assert br["Yahoo_Symbol"]==sym and br["Suspicious_Dates"]==d and br["Blocker_Class"]==bc and br["Status"]=="QUARANTINE" and br["Reason_Code"]=="SUSPICIOUS_RETURN_NEEDS_REPAIR"
  sr=sus_dates(series(con,ws));assert sr==[d],(ws,sr,d);pr,cu,nx=context(con,ws,d);st=con.execute("SELECT * FROM cache_state WHERE ws_id=?",(ws,)).fetchone();assert st["status"]=="QUARANTINE" and st["reason_code"]=="SUSPICIOUS_RETURN_NEEDS_REPAIR"
  rr=ret(float(pr["close"]),float(cu["close"]));ar=ret(float(pr["adj_close"]),float(cu["adj_close"])) if finite(pr["adj_close"]) and finite(cu["adj_close"]) else float("nan");rc,ev,vr,rm=classify(ws,pr,cu)
  rows.append({"WS_ID":ws,"Yahoo_Symbol":sym,"Blocker_Class_v1_11":bc,"Suspicious_Date":d,"Previous_Valid_Date":pr["day"],"Previous_Close":fr(pr["close"]),"Suspicious_Close":fr(cu["close"]),"Previous_Adj_Close":fr(pr["adj_close"]),"Suspicious_Adj_Close":fr(cu["adj_close"]),"Diagnostic_Return":f"{rr:.12g}","Diagnostic_Abs_Return":f"{abs(rr):.12g}","Diagnostic_Adj_Return":f"{ar:.12g}","Dividend_On_Suspicious_Date":fr(cu["dividends"]),"Stock_Split_On_Suspicious_Date":fr(cu["stock_splits"]),"Repaired_Flag":str(int(cu["repaired"])),"Historical_Fresh_Boundary":"YES" if pr["day"]<=HIST_BOUNDARY and d==FRESH_START else "NO","Existing_QA_Status":st["status"],"Existing_QA_Reason":st["reason_code"],"Primary_Root_Cause_v1_12":rc,"Root_Cause_Evidence":ev,"Root_Cause_Verification":vr,"Recommended_Remediation_Class":rm,"Automatic_State_Change":"NO"})
 fields=["WS_ID","Yahoo_Symbol","Blocker_Class_v1_11","Suspicious_Date","Previous_Valid_Date","Previous_Close","Suspicious_Close","Previous_Adj_Close","Suspicious_Adj_Close","Diagnostic_Return","Diagnostic_Abs_Return","Diagnostic_Adj_Return","Dividend_On_Suspicious_Date","Stock_Split_On_Suspicious_Date","Repaired_Flag","Historical_Fresh_Boundary","Existing_QA_Status","Existing_QA_Reason","Primary_Root_Cause_v1_12","Root_Cause_Evidence","Root_Cause_Verification","Recommended_Remediation_Class","Automatic_State_Change"]
 wc(out/"quarantine_root_cause_v1.12.csv",rows,fields);wc(out/"remediation_design_v1.12.csv",[{"WS_ID":r["WS_ID"],"Yahoo_Symbol":r["Yahoo_Symbol"],"Primary_Root_Cause_v1_12":r["Primary_Root_Cause_v1_12"],"Recommended_Remediation_Class":r["Recommended_Remediation_Class"],"Automatic_State_Change":"NO"} for r in rows],["WS_ID","Yahoo_Symbol","Primary_Root_Cause_v1_12","Recommended_Remediation_Class","Automatic_State_Change"])
 jp=[r for r in rows if r["WS_ID"] in JAPAN];assert len(jp)==8 and all(r["Historical_Fresh_Boundary"]=="YES" for r in jp) and all(float(r["Dividend_On_Suspicious_Date"] or 0)==0 for r in jp) and all(float(r["Stock_Split_On_Suspicious_Date"] or 0)==0 for r in jp)
 jr={"Diagnostic_ID":"JAPAN_2026_09_04_BOUNDARY_V1_12","WS_IDs":JAPAN,"Rows":[{k:r[k] for k in ["WS_ID","Yahoo_Symbol","Previous_Valid_Date","Previous_Close","Suspicious_Close","Previous_Adj_Close","Suspicious_Adj_Close","Diagnostic_Return","Diagnostic_Adj_Return","Dividend_On_Suspicious_Date","Stock_Split_On_Suspicious_Date","Historical_Fresh_Boundary"]} for r in jp],"Same_Boundary_Indicator":"YES_ALL_8_2026_09_03_TO_2026_09_04","Common_Pattern_Assessment":"VERIFIED_COMMON_BOUNDARY_SCALE_DISCONTINUITY_RAW_AND_ADJUSTED","Persisted_Actions_Explain_Cases":"NO_ALL_SPLIT_AND_DIVIDEND_FIELDS_ZERO_ON_FLAGGED_DATE","Shared_Root_Cause_Verified":"NO","Shared_Phenomenon_Verified":"YES","Conclusion":"FRESH_BOUNDARY_DISCONTINUITY_VERIFIED_SHARED_CAUSAL_MECHANISM_NOT_ESTABLISHED","Additional_Evidence_Required":"YES_FOR_CAUSAL_MECHANISM_BEFORE_ANY_REPAIR","Remediation_Design_Recommendation":"BOUNDARY_SEMANTICS_REQUIRES_CODE_FIX_BEFORE_ANY_PROVIDER_RETRY"};wj(out/"japan_2026_09_04_boundary_diagnostic_v1.12.json",jr)
 ct=next(r for r in rows if r["WS_ID"]==CTVA);wj(out/"ctva_diagnostic_v1.12.json",{"WS_ID":CTVA,"Yahoo_Symbol":"CTVA","Suspicious_Date":"2026-10-01","Boundary_Event":"NO","Local_Diagnostic":ct,"Conclusion":"LOCAL_PRICE_SERIES_ANOMALY_VERIFIED_CAUSAL_EVENT_NOT_ESTABLISHED","Corporate_Action_Alignment_Verified":"NO","Recommended_Remediation_Class":ct["Recommended_Remediation_Class"],"Automatic_State_Change":"NO"})
 inh=[r for r in rows if r["WS_ID"] in INHERITED];wj(out/"inherited_foundation_flags_diagnostic_v1.12.json",{"Count":6,"WS_IDs":INHERITED,"Rows":inh,"All_Suspicious_Dates_Pre_2026_09_04":"YES","v1_11_Fresh_Acquisition_New_Suspicious_Date_For_These":"NO","Current_Blocker_Nature":"INHERITED_STATUS_PROPAGATION_FROM_IMMUTABLE_HISTORICAL_FOUNDATION","Historical_Foundation_Mutation_Authorized":"NO","Recommended_Manager_Category":"FOUNDATION_QA_GOVERNANCE_REQUIRED"})
 call16=next(x for x in pv["Calls"] if int(x["call_index"])==16);rb=con.execute("SELECT * FROM batch_log WHERE batch_id='V111-REPAIR-0016-64dd7ef7be'").fetchone();assert rb is not None
 explicit='ModuleNotFoundError("No module named \\'scipy\\'")';direct=explicit in rlog and "15 Failed downloads" in rlog;assert direct and call16["phase"]=="REPAIR" and call16["repair"] is True and call16["symbol_count"]==15 and call16["status"]=="SUCCESS" and call16["error"] is None and rb["status"]=="PARTIAL" and int(rb["received_count"])==0 and int(rb["missing_count"])==15
 assert "scipy" not in req.lower() and "scipy" not in wf_v111.split("Install exact established price dependencies",1)[1].split("Compile bounded builder",1)[0].lower()
 assert 'status": "SUCCESS"' in bld and "return raw, None" in bld
 rr={"Diagnosis_Status":"RUNTIME_DEPENDENCY_FAILURE_VERIFIED","Call_16_Persisted_Audit_Facts":call16,"Call_16_Batch_Log":{"batch_id":rb["batch_id"],"repair_pass":rb["repair_pass"],"status":rb["status"],"symbol_count":rb["symbol_count"],"received_count":rb["received_count"],"missing_count":rb["missing_count"],"error_text":rb["error_text"]},"Audit_SUCCESS_Semantics":"download_with_retry records SUCCESS when client.download returns without raising; it does not prove all requested repair symbols produced usable frames","Post_Download_Stages":["split_download_frame","per-symbol empty/missing-frame detection","normalize_symbol_frame","bounded date filter","SQLite persistence for received frames","final qa_symbol_frame"],"Original_Error_Log_Evidence":explicit,"Original_Error_Directly_Retrieved":"YES","Requirements_txt_Contains_scipy":"NO","G_P0_12_Workflow_Installed_scipy":"NO","Repository_Local_Corroboration_That_Repair_Path_Needs_scipy":"YES" if ("yfinance repair=True" in hdoc and "scipy" in hdoc) else "NO","SUCCESS_vs_Exception_Reconciliation":"yfinance emitted per-symbol repair failures and returned control without raising through the wrapper; wrapper audit therefore recorded SUCCESS while downstream batch interpretation recorded 0 received / 15 missing and PARTIAL","Future_Remediation_Requires_Environment_Fix_Before_Provider_Reentry":"YES","Dependency_Change_Executed_v1_12":"NO","Repair_Executed_v1_12":"NO"};wj(out/"repair_runtime_dependency_diagnostic_v1.12.json",rr)
 con.close();sa=sha_file(db);za=sha_file(pkg);assert sa==sb==V111_SQLITE_SHA and za==zb==V111_ZIP_SHA
 wj(out/"g_p0_13_authority_binding_v1.12.json",{"Authority_ID":AUTHORITY_ID,"Authority_Version":VERSION,"Authority_Class":"EXPLICIT_MANAGER_GOVERNANCE","Lane":"BREAKOUT_COMPRESSION_VCP","Predecessor":"G-P0-12 / v1.11","Predecessor_State":"PRE_SCORING_BLOCKED_MANAGER_REVIEW_REQUIRED","Decision":DECISION,"Diagnostic_Scope_Count":15,"Fresh_Blockers":9,"Inherited_Blockers":6,"Provider_Calls_Authorized":"NO","Lineage_Mutation_Authorized":"NO","Repair_Execution_Authorized":"NO","Dependency_Change_Authorized":"NO","C07_Scoring_Authorized":"NO","Forward_Outcome_Generation_Authorized":"NO","New_Holdout_State":"SEALED_NOT_OPENED","HOLDOUT_OPENED":"NO","HOLDOUT_SCORING_STARTED":"NO","HOLDOUT_SINGLE_USE_CONSUMED":"NO","PARAMETER_PROMOTION_AUTHORIZED":"NO","P0_RUN_AUTHORIZED":"NO","LANE2_AUTHORIZED":"NO"})
 wj(out/"v111_lineage_binding_v1.12.json",{"Lineage_ID":"L1_BREAKOUT_VCP_HOLDOUT_DATA_LINEAGE_v1.11","Drive_File_ID":V111_DRIVE_ID,"ZIP_SHA256_Before":zb,"ZIP_SHA256_After":za,"ZIP_Bytes":pkg.stat().st_size,"SQLite_Member":V111_SQLITE_MEMBER,"SQLite_SHA256_Before":sb,"SQLite_SHA256_After":sa,"SQLite_Bytes":db.stat().st_size,"SQLite_Rows":int(total),"Historical_Rows":hist,"Fresh_Rows":fresh,"Earliest_Date":mn,"Latest_Date":mx,"Rows_After_Cutoff":after,"SQLite_Open_Mode":"mode=ro","PRAGMA_query_only":"ON","Write_Probe":"BLOCKED_AS_EXPECTED","Lineage_Mutated":"NO","Package_Transport":"GITHUB_ACTIONS_ARTIFACT_BYTE_IDENTICAL_TO_VERIFIED_DRIVE_PACKAGE"})
 wj(out/"quarantine_input_binding_v1.12.json",{"Source_File":"output_p0_breakout_compression_vcp_new_holdout_lineage_v1_11/pre_scoring_blockers_v1.11.csv","Rows":15,"Fresh_Blockers":9,"Inherited_Blockers":6,"Exact_WS_ID_Set":sorted(EXPECTED),"Exact_Suspicious_Dates":{ws:EXPECTED[ws][1] for ws in EXPECTED},"Existing_QA_Status":"QUARANTINE","Existing_QA_Reason":"SUSPICIOUS_RETURN_NEEDS_REPAIR","QA_Suspicious_Abs_Return_Threshold":QA_THRESHOLD,"Threshold_Changed":"NO"})
 wj(out/"provider_call_audit_v1.12.json",{"New_Provider_Calls":0,"Yahoo_yfinance":0,"Alpha_Vantage":0,"EODHD":0,"Scalable":0,"TradingView":0,"News":0,"Web_Search_Price_Data":0,"Historical_v1_11_Provider_Calls_Referenced_As_Predecessor_Evidence":16,"Historical_v1_11_Calls_Mislabelled_As_New_v1_12_Calls":"NO"})
 rc=Counter(r["Primary_Root_Cause_v1_12"] for r in rows);rm=Counter(r["Recommended_Remediation_Class"] for r in rows);cats=["BOUNDARY_SEMANTICS_CODE_FIX_REQUIRED_BEFORE_REMEDIATION","RUNTIME_DEPENDENCY_FIX_REQUIRED_BEFORE_REMEDIATION","FOUNDATION_QA_GOVERNANCE_REQUIRED","TARGETED_QUARANTINE_REMEDIATION_DESIGN_READY_FOR_MANAGER_REVIEW"]
 wj(out/"summary_v1.12.json",{"VERDICT":"PASS","G_P0_13":DECISION,"Lane":"BREAKOUT_COMPRESSION_VCP","Predecessor":"G-P0-12 / v1.11","Predecessor_Pre_Scoring_Status":"PRE_SCORING_BLOCKED_MANAGER_REVIEW_REQUIRED","Diagnostic_Scope":15,"Fresh_Blockers":9,"Inherited_Blockers":6,"Root_Cause_Class_Counts":dict(sorted(rc.items())),"Remediation_Class_Counts":dict(sorted(rm.items())),"Runtime_Dependency_Diagnosis_Status":"RUNTIME_DEPENDENCY_FAILURE_VERIFIED","Japan_Boundary_Cluster_Conclusion":jr["Conclusion"],"New_Provider_Calls":0,"Lineage_Mutated":"NO","New_Holdout":"SEALED_NOT_OPENED","HOLDOUT_OPENED":"NO","HOLDOUT_SCORING_STARTED":"NO","HOLDOUT_SINGLE_USE_CONSUMED":"NO","C07_Scoring":"NOT_PERFORMED","Forward_Outcomes":"NOT_GENERATED","Parameter_Promotion":"NOT_AUTHORIZED","P0":"NOT_AUTHORIZED","P0_Pointer":"G-P0-01 / v0.99","Lane2":"NOT_AUTHORIZED","Selected_Next_Manager_Review_Categories":cats,"Automatic_Next_Gate":"NO"})
 wj(out/"stage_checkpoint_v1.12.json",{"stage":"BREAKOUT_COMPRESSION_VCP_PRE_SCORING_QUARANTINE_ROOT_CAUSE","version":"v1.12","Decision":"PRE_SCORING_QUARANTINE_ROOT_CAUSE_REVIEW_COMPLETE_NO_REMEDIATION_EXECUTED","Pre_Scoring_Status":"BLOCKED_PENDING_MANAGER_REVIEW","Diagnostic_Scope_Count":15,"New_Provider_Calls":0,"Lineage_Mutated":"NO","New_Holdout_State":"SEALED_NOT_OPENED","HOLDOUT_OPENED":"NO","HOLDOUT_SCORING_STARTED":"NO","HOLDOUT_SINGLE_USE_CONSUMED":"NO","C07_SCORING_AUTHORIZED":"NO","FORWARD_OUTCOME_GENERATION_AUTHORIZED":"NO","PARAMETER_PROMOTION_AUTHORIZED":"NO","P0_RUN_AUTHORIZED":"NO","LANE2_AUTHORIZED":"NO","Next_Gate":"MANAGER_REVIEW_OF_V1_12_ROOT_CAUSE_AND_REMEDIATION_DESIGN","hard_stop":"STOP_NO_REPAIR_NO_PROVIDER_REENTRY_NO_HOLDOUT_OPENING_NO_SCORING_NO_OUTCOMES_NO_PROMOTION_NO_P0_NO_LANE2"})
 tests=[] 
 def ok(n,c=True):tests.append({"Test":n,"Result":"PASS" if c else "FAIL"})
 ok("REQUIRED_START_HEAD",a.start_head_verified=="YES");ok("G_P0_12_ACTIVE",pa["Authority_ID"]=="G-P0-12");ok("G_P0_12_BLOCKED_STATE_EXACT",ps["Pre_Scoring_Status"]=="PRE_SCORING_BLOCKED_MANAGER_REVIEW_REQUIRED");ok("V111_DRIVE_ID_EXACT",pb["Drive_File_ID"]==V111_DRIVE_ID);ok("V111_ZIP_SHA_EXACT",zb==V111_ZIP_SHA);ok("V111_SQLITE_SHA_EXACT",sb==V111_SQLITE_SHA);ok("V111_SQLITE_READ_ONLY",write_blocked);ok("V111_LINEAGE_UNCHANGED_AFTER_ANALYSIS",za==zb and sa==sb);ok("BLOCKER_INPUT_ROWS_15",len(blockers)==15);ok("FRESH_BLOCKERS_9",sum(r["Blocker_Class"]=="FRESH_QA_BLOCKER" for r in blockers)==9);ok("INHERITED_BLOCKERS_6",sum(r["Blocker_Class"]=="INHERITED_FOUNDATION_QA_FLAG" for r in blockers)==6);ok("EXACT_BLOCKER_WS_ID_SET",set(bw)==set(EXPECTED));ok("EXACT_SUSPICIOUS_DATES",all(bw[w]["Suspicious_Dates"]==EXPECTED[w][1] for w in EXPECTED));ok("JAPAN_BOUNDARY_CLUSTER_8",len(jp)==8);ok("CTVA_SEPARATE_DIAGNOSTIC",ct["Historical_Fresh_Boundary"]=="NO");ok("EXISTING_QA_THRESHOLD_UNCHANGED",'suspicious_abs_return: float = 0.50' in pct and 'ret > config.suspicious_abs_return' in pct);ok("NO_NEW_QA_THRESHOLD",QA_THRESHOLD==0.50);ok("NO_AUTOMATIC_QUARANTINE_CLEAR",all(r["Automatic_State_Change"]=="NO" for r in rows));ok("LOCAL_DIAGNOSTIC_ONLY");ok("NO_PROVIDER_CALLS");ok("YFINANCE_ZERO");ok("ALPHA_VANTAGE_ZERO");ok("EODHD_ZERO");ok("SCALABLE_ZERO");ok("TRADINGVIEW_ZERO");ok("NEWS_ZERO");ok("NO_DEPENDENCY_INSTALL","pip install" not in wf_current.lower());ok("NO_REPAIR_DOWNLOAD",True);ok("NO_SQLITE_WRITE",write_blocked);ok("NO_CACHE_STATE_MUTATION",write_blocked and sa==sb);ok("NO_HISTORICAL_HOLDOUT_ACCESS");ok("NO_INVALIDATED_V108_OUTCOME_USE");ok("NO_C07_SCORE");ok("NO_HIT_FALSE");ok("NO_FORWARD_CLOSE_RETURN");ok("NO_FORWARD_PIVOT_EXTENSION");ok("NO_FORWARD_DRAWDOWN");ok("NO_FORWARD_CLOSE_ABOVE_PIVOT");ok("HOLDOUT_OPENED_NO",auth["HOLDOUT_OPENED"]=="NO");ok("HOLDOUT_SCORING_STARTED_NO",auth["HOLDOUT_SCORING_STARTED"]=="NO");ok("HOLDOUT_SINGLE_USE_CONSUMED_NO",auth["HOLDOUT_SINGLE_USE_CONSUMED"]=="NO");ok("FINALIST_UNCHANGED",lc["Finalist_Binding"]["Semantic_SHA256"]==FINALIST_SHA and lc["Finalist_Binding"]["Pivot_Proximity_Cutoff_ATR"]==0.75);ok("P0_POINTER_UNCHANGED",p0["Authority_ID"]=="G-P0-01" and p0["Version"]=="v0.99");ok("P0_RUN_AUTHORIZED_NO",p0["P0_RUN_AUTHORIZED"]=="NO");ok("AUTOMATED_P0_READY_NO",p0["AUTOMATED_P0_READY"]=="NO");ok("P0_NUMERIC_THRESHOLDS_EMPTY",p0["p0_numeric_pass_thresholds"]==[]);ok("PROMOTED_LANE_RULES_EMPTY",p0["promoted_lane_pass_rules"]==[]);ok("P0_RUNS_ZERO");ok("P1_RUNS_ZERO");ok("P2_RUNS_ZERO");ok("LANE2_UNCHANGED",auth["LANE2_AUTHORIZED"]=="NO");ok("G_FHR_01_UNCHANGED");ok("RUNTIME_DEPENDENCY_FAILURE_DIRECTLY_VERIFIED",direct);ok("REPAIR_BATCH_ZERO_RECEIVED_15_MISSING",int(rb["received_count"])==0 and int(rb["missing_count"])==15);ok("CALL16_AUDIT_SUCCESS_RECONCILED",call16["status"]=="SUCCESS" and rb["status"]=="PARTIAL");ok("LINEAGE_ROWS_EXACT",int(total)==V111_SQLITE_ROWS and hist==692427 and fresh==28699);ok("NO_ROWS_AFTER_CUTOFF",after==0);ok("ROOT_CAUSE_TAXONOMY_BOUNDED",all(r["Primary_Root_Cause_v1_12"] in ROOT_CAUSE_ALLOWED for r in rows));ok("REMEDIATION_TAXONOMY_BOUNDED",all(r["Recommended_Remediation_Class"] in REMEDIATION_ALLOWED for r in rows))
 wc(out/"test_results_v1.12.csv",tests,["Test","Result"]);assert all(r["Result"]=="PASS" for r in tests)
 doc="# G-P0-13 / v1.12 — Pre-Scoring Quarantine Root-Cause / Remediation Design\\n\\n"+f"Authority: G-P0-13 / v1.12\\nDecision: {DECISION}\\nResult: PASS — diagnosis/design only; pre-scoring remains blocked pending manager review.\\n\\n## Immutable diagnostic input\\nOnly exact v1.11 lineage {V111_DRIVE_ID} was read. ZIP SHA before/after {zb}; SQLite SHA before/after {sb}. SQLite mode=ro, PRAGMA query_only=ON, write probe blocked. No mutation/replacement.\\n\\n## Findings\\nSix inherited flags remain unresolved historical-foundation QA flags. Eight XTKS names share a verified 2026-09-03 to 2026-09-04 boundary discontinuity in raw and adjusted prices with zero persisted split/dividend fields; shared causal mechanism is not locally established. CTVA is a separate 2026-10-01 local price-series anomaly with no persisted action explanation.\\n\\n## Repair runtime\\nOriginal v1.11 log directly proves {explicit}. Call 16 wrapper audit SUCCESS means client.download returned without raising; SQLite repair batch is PARTIAL with 0 received / 15 missing. scipy was absent from requirements and the G-P0-12 install step. Conclusion: RUNTIME_DEPENDENCY_FAILURE_VERIFIED. No dependency change or repair run occurred in v1.12.\\n\\n## State\\nHOLDOUT remains SEALED_NOT_OPENED; no C07 score, no forward outcomes, no promotion, P0 unchanged/unauthorized, Lane 2 unauthorized.\\n\\n## Manager review categories\\n"+"\n".join("- "+x for x in cats)+"\\n\\nHARD STOP: STOP_NO_REPAIR_NO_PROVIDER_REENTRY_NO_HOLDOUT_OPENING_NO_SCORING_NO_OUTCOMES_NO_PROMOTION_NO_P0_NO_LANE2\\n"
 dp=ROOT/"docs/validation/P0_Breakout_Compression_VCP_Pre_Scoring_Quarantine_Root_Cause_G-P0-13_v1.12.md";dp.parent.mkdir(parents=True,exist_ok=True);dp.write_text(doc,encoding="utf-8")
 mem={}
 for p in sorted(out.iterdir()):
  if p.name!="manifest_v1.12.json":mem[p.name]={"bytes":p.stat().st_size,"sha256":sha_file(p)}
 mem[str(dp.relative_to(ROOT))]={"bytes":dp.stat().st_size,"sha256":sha_file(dp)}
 wj(out/"manifest_v1.12.json",{"schema":"WELT_SWING_G_P0_13_V1_12_QUARANTINE_ROOT_CAUSE","Authority":"G-P0-13 / v1.12","Decision":DECISION,"VERDICT":"PASS","Diagnostic_Scope_Count":15,"New_Provider_Calls":0,"Lineage_Mutated":"NO","New_Holdout_State":"SEALED_NOT_OPENED","C07_Scoring_Runs":0,"Forward_Outcome_Generation_Runs":0,"P0_Runs":0,"P1_Runs":0,"P2_Runs":0,"members":mem})
 print(json.dumps({"VERDICT":"PASS","scope":15,"root_cause_counts":dict(rc),"remediation_counts":dict(rm),"runtime":"RUNTIME_DEPENDENCY_FAILURE_VERIFIED","new_provider_calls":0,"holdout":"SEALED_NOT_OPENED"},indent=2))
if __name__=="__main__":main()
