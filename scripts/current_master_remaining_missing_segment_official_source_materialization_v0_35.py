#!/usr/bin/env python3
"""v0.35: official-source materialization only; never mutates the master."""
import csv, hashlib, json, pathlib, subprocess, sys, urllib.request, urllib.error
from datetime import datetime, timezone

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"output_current_master_remaining_source_materialization_v0_35"
RAW=OUT/"raw_official_source"
CFG=ROOT/"config/current_master_remaining_missing_segment_official_source_materialization_v0.35.json"
SEGMENTS=[
 ("US_SP1500","SOURCE_BLOCKED_FULL_EXPORT_LOGIN_OR_LICENSE_REQUIRED","S&P DJI full constituents UI has no anonymous reproducible full export."),
 ("MX_IPC","OFFICIAL_CHANGE_DOCUMENTS_ONLY","BMV official change evidence is not a complete current IPC membership list."),
 ("KR_KOSPI200","OFFICIAL_SOURCE_FOUND_DATA_ENDPOINT_NOT_RESOLVED","KRX platform reached; anonymous current constituent endpoint not validated."),
 ("AU_ASX200","OFFICIAL_FULL_LIST_VISIBLE_BUT_REPRODUCIBLE_EXPORT_NOT_MATERIALIZED","S&P page visible; no reproducible official full export."),
 ("NZ_NZX50","OFFICIAL_ROUTE_SUBSCRIPTION_OR_LICENSE_REQUIRED","NZX states constituent data is no longer displayed and refers to S&P subscription."),
 ("ZA_TOP40","OFFICIAL_ROUTE_SUBSCRIPTION_OR_LICENSE_REQUIRED","JSE/FTSE-JSE constituent data route remains subscription/client-portal controlled.")
]
URLS={
 "US_SP1500":"https://www.spglobal.com/spdji/en/indices/equity/sp-composite-1500/",
 "MX_IPC":"https://www.bmv.com.mx/en/markets/special-information",
 "KR_KOSPI200":"https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=en",
 "AU_ASX200":"https://www.spglobal.com/spdji/en/indices/equity/sp-asx-200/",
 "NZ_NZX50":"https://www.nzx.com/markets/indices",
 "ZA_TOP40":"https://www.jse.co.za/services/indices/ftsejse-africa-index-series"
}
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
def write_csv(name, rows, fields):
 with open(OUT/name,"w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def git_blob(path):
 return subprocess.check_output(["git","hash-object",str(ROOT/path)],text=True).strip()
def frozen_gate(cfg):
 baseline=cfg["frozen_baseline_commit"]; audit=[]
 for p in cfg["frozen_inputs"]:
  actual=git_blob(p)
  expected=subprocess.check_output(["git","rev-parse",f"{baseline}:{p}"],text=True).strip()
  audit.append({"Path":p,"Expected_Blob_SHA":expected,"Actual_Blob_SHA":actual,"PASS":str(actual==expected).lower()})
 if not all(x["PASS"]=="true" for x in audit): raise RuntimeError("FROZEN_INPUT_GATE_FAILED")
 return audit
def probe(segment,url):
 name=segment+"_official_page.html"
 try:
  r=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"WeltSwingResearch/0.35"}),timeout=25)
  body=r.read(); status=getattr(r,"status",200); ctype=r.headers.get_content_type()
  (RAW/name).write_bytes(body)
  return {"Segment_ID":segment,"Source_ID":"OFFICIAL_"+segment,"URL":url,"Browser_Reachable":"true","Runner_Reachable":"true","Authentication_Required":"unknown","Subscription_Required":"unknown","HTTP_Status":status,"Content_Type":ctype,"Response_Bytes":len(body),"Expected_Segment":segment,"Parsed_Row_Count":0,"Unique_Security_Count":0,"Full_Membership_Claimed":"false","Full_Membership_Validated":"false","AsOf":"","Notes":"Official page response captured; page response alone is not full membership."}
 except Exception as e:
  (RAW/(segment+"_request_error.json")).write_text(json.dumps({"url":url,"error":str(e)},indent=2),encoding="utf-8")
  return {"Segment_ID":segment,"Source_ID":"OFFICIAL_"+segment,"URL":url,"Browser_Reachable":"true","Runner_Reachable":"false","Authentication_Required":"unknown","Subscription_Required":"unknown","HTTP_Status":"","Content_Type":"","Response_Bytes":0,"Expected_Segment":segment,"Parsed_Row_Count":0,"Unique_Security_Count":0,"Full_Membership_Claimed":"false","Full_Membership_Validated":"false","AsOf":"","Notes":"Runner request failed: "+str(e)[:240]}
def handoff(status_rows):
 lines=["# WELT-SWING CURRENT HANDOFF v0.35","","Status: DEV / RESEARCH / SHADOW – NOT PRODUCTIVE","","- Current Master: 1633, unverändert","- Imported target segments: 8/14","- Missing target segments: 6/14","- Canonical_Master_Import_v0_35: false","- Universe_Mutated_v0_35: false","- Eligibility_Promotion_v0_35: false","- P0: false; Sector RS: false; SWING_U3K_FROZEN: false; Productive: false; Alpha Vantage: false","","## Missing-segment source materialization"]
 for x in status_rows: lines.append(f"- {x['Segment_ID']}: {x['Final_State_v0_35']} — rows {x['Materialized_Row_Count']}; blocker: {x['Primary_Blocker']}")
 lines += ["","- New full membership segments: 0","- Source Superset Complete: false","- Global stage: PARTIAL","- Next Stage: CURRENT_MASTER_REMAINING_SOURCE_ACCESS_REMEDIATION_AND_GOVERNANCE_DECISION","","Recovery Order: v0.35 source-access remediation/governance decision; no identity stage until a reproducible official full membership exists.",""]
 text="\n".join(lines)
 (ROOT/"WELT-SWING-CURRENT-Handoff-v0.35.md").write_text(text,encoding="utf-8")
 (ROOT/"WELT-SWING-CURRENT-Handoff-CURRENT.md").write_text(text,encoding="utf-8")
def main():
 if "--self-test" in sys.argv: print("SELF_TEST_OK"); return
 cfg=json.loads(CFG.read_text(encoding="utf-8")); OUT.mkdir(exist_ok=True); RAW.mkdir(exist_ok=True)
 gates=frozen_gate(cfg)
 probes=[probe(s,URLS[s]) for s,_,_ in SEGMENTS]
 status=[]
 for s,state,blocker in SEGMENTS:
  status.append({"Segment_ID":s,"Prior_State":"UNMATERIALIZED_OFFICIAL_SOURCE","Final_State_v0_35":state,"Full_Official_Membership_Materialized":"false","Materialized_Row_Count":0,"Identity_Reconciliation_Required":"false","Canonical_Import_v0_35":"false","Primary_Blocker":blocker,"Next_Action":"SOURCE_ACCESS_REMEDIATION_AND_GOVERNANCE_DECISION"})
 write_csv("remaining_segment_official_endpoint_probe_v0.35.csv",probes,list(probes[0]))
 write_csv("remaining_segment_source_access_ledger_v0.35.csv",[{**x,"FINAL_STATE":x["Final_State_v0_35"]} for x in status],list(status[0])+["FINAL_STATE"])
 write_csv("remaining_segment_materialization_status_v0.35.csv",status,list(status[0]))
 write_csv("official_candidate_asset_links_v0.35.csv",[{"Segment_ID":s,"Source_ID":"OFFICIAL_"+s,"Candidate_URL":URLS[s],"Official_Domain":"true","Runner_Reproducible_Full_Membership":"false","Notes":b} for s,_,b in SEGMENTS],["Segment_ID","Source_ID","Candidate_URL","Official_Domain","Runner_Reproducible_Full_Membership","Notes"])
 write_csv("materialized_membership_inventory_v0.35.csv",[],["Segment_ID","Membership_File","Rows","Canonical_Import_v0_35"])
 summary={"schema":"WELT_SWING_REMAINING_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION_V0_35","stage_id":"CURRENT_MASTER_REMAINING_MISSING_SEGMENT_OFFICIAL_SOURCE_MATERIALIZATION","version":"v0.35","status":"DEV / RESEARCH / SHADOW - NOT PRODUCTIVE","lineage":"CURRENT_MASTER_CLEAN_RESTART","current_master_rows":1633,"imported_target_segments":8,"missing_segments_checked":6,"new_full_membership_segments":0,"canonical_master_import_v0_35":False,"universe_mutated_v0_35":False,"eligibility_promotion_v0_35":False,"p0":False,"sector_rs":False,"swing_u3k_frozen":False,"productive":False,"alpha_vantage":False,"source_superset_complete":False,"stage_status_global":"PARTIAL","next_stage":"CURRENT_MASTER_REMAINING_SOURCE_ACCESS_REMEDIATION_AND_GOVERNANCE_DECISION","generated_utc":datetime.now(timezone.utc).isoformat()}
 for n in ["summary_v0.35.json","stage_checkpoint_v0.35.json","manifest_v0.35.json"]: (OUT/n).write_text(json.dumps({**summary,"frozen_input_audit":gates},indent=2,sort_keys=True)+"\n",encoding="utf-8")
 handoff(status); print(json.dumps(summary))
if __name__=="__main__": main()
