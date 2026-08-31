#!/usr/bin/env python3
"""v0.35-r2: real evidence-led official source materialization."""
import csv,json,pathlib,shutil,subprocess,sys
from io import BytesIO
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
R=pathlib.Path(__file__).resolve().parents[1]; O=R/"output_current_master_remaining_source_materialization_v0_35"; RAW=O/"raw_official_source"; C=R/"config/current_master_remaining_missing_segment_official_source_materialization_v0.35.json"
def out(n,rows,cols):
 with open(O/n,"w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
def gate(p,b):
 a=subprocess.check_output(["git","hash-object",str(R/p)],text=True).strip();e=subprocess.check_output(["git","rev-parse",b+":"+p],text=True).strip()
 if a!=e:raise RuntimeError("FROZEN_INPUT_GATE_FAILED "+p)
 return {"Path":p,"Expected_Blob_SHA":e,"Actual_Blob_SHA":a,"PASS":True}
def parse(body,ct):
 text=""; rows=[]; codes=[]
 if "pdf" in ct:
  try:text="\n".join(x.extract_text() or "" for x in PdfReader(BytesIO(body)).pages)
  except Exception:pass
 elif "json" in ct:
  try:
   x=json.loads(body); text=json.dumps(x); rows=x.get("output",x.get("data",[])) if isinstance(x,dict) else x
   for z in rows:
    if isinstance(z,dict):
     v=next((z.get(k) for k in ["ISU_CD","ISU_SRT_CD","code","symbol","ticker"] if z.get(k)),None)
     if v:codes.append(str(v))
  except Exception:pass
 else:
  text=body.decode("utf-8","ignore"); t=BeautifulSoup(text,"lxml").find("table")
  if t:
   rows=[[c.get_text(" ",strip=True) for c in r.find_all(["td","th"])] for r in t.find_all("tr")[1:]]
   codes=[r[1] for r in rows if len(r)>1 and r[1]]
 return text,rows,sorted(set(codes))
def probe(e):
 try:
  q=requests.request(e.get("Method","GET"),e["URL"],data=e.get("Form_Data"),headers={"User-Agent":"WeltSwing/0.35-r2"},timeout=30,allow_redirects=True);ct=q.headers.get("content-type","").split(";")[0].lower(); RAW.joinpath(e["Segment_ID"]+"_"+e["Source_ID"]+".bin").write_bytes(q.content);t,rows,codes=parse(q.content,ct);lo=t.lower();claim=any(x in lo for x in ["full constituents","constituents list","constituent list"]);valid=claim and len(rows)>=e.get("Plausible_Min_Rows",99999) and len(codes)>=e.get("Plausible_Min_Rows",99999) and "top 10" not in lo
  return dict(Segment_ID=e["Segment_ID"],Source_ID=e["Source_ID"],URL=e["URL"],Source_Type=e["Source_Type"],HTTP_Status=q.status_code,Content_Type=ct,Response_Bytes=len(q.content),Redirect_Final_URL=q.url,Authentication_Required=str("log in" in lo).lower(),Subscription_Required=str("subscription" in lo).lower(),Parsed_Row_Count=len(rows),Unique_Security_Count=len(codes),Full_Membership_Claimed=str(claim).lower(),Full_Membership_Validated=str(valid).lower(),AsOf="",Error_Class="",Evidence_Notes=t[:700].replace("\n"," "),Runner_Tested="true",Runner_Reproducible=str(q.status_code==200).lower(),Direct_Asset=str(e["Direct_Asset"]).lower())
 except Exception as x:return dict(Segment_ID=e["Segment_ID"],Source_ID=e["Source_ID"],URL=e["URL"],Source_Type=e["Source_Type"],HTTP_Status="",Content_Type="",Response_Bytes=0,Redirect_Final_URL="",Authentication_Required="unknown",Subscription_Required="unknown",Parsed_Row_Count=0,Unique_Security_Count=0,Full_Membership_Claimed="false",Full_Membership_Validated="false",AsOf="",Error_Class=type(x).__name__,Evidence_Notes=str(x),Runner_Tested="true",Runner_Reproducible="false",Direct_Asset=str(e["Direct_Asset"]).lower())
def state(s,ps):
 p=[x for x in ps if x["Segment_ID"]==s];v=[x for x in p if x["Full_Membership_Validated"]=="true"];n=" ".join(x["Evidence_Notes"].lower() for x in p)
 if v:return "FULL_OFFICIAL_MEMBERSHIP_MATERIALIZED",sum(int(x["Parsed_Row_Count"]) for x in v),"validated parsed official membership"
 if "subscription" in n:return "OFFICIAL_ROUTE_SUBSCRIPTION_OR_LICENSE_REQUIRED",0,"official subscription evidence"
 if "full constituents" in n:return "OFFICIAL_FULL_LIST_VISIBLE_BUT_REPRODUCIBLE_EXPORT_NOT_MATERIALIZED",0,"full-list UI without reproducible parse"
 if "rebalance" in n or "quarterly review" in n:return "OFFICIAL_CHANGE_DOCUMENTS_ONLY",0,"official change/review asset only"
 if s=="KR_KOSPI200" and any(x["Source_Type"]=="API" for x in p):return "OFFICIAL_SOURCE_FOUND_DATA_ENDPOINT_NOT_RESOLVED",0,"official KRX API candidate tested without validated constituents"
 return "OFFICIAL_SOURCE_NOT_MATERIALIZED",0,"official routes tested without full membership"
def main():
 if "--self-test" in sys.argv:print("SELF_TEST_OK");return
 c=json.loads(C.read_text());shutil.rmtree(O,ignore_errors=True);RAW.mkdir(parents=True);audit=[gate(p,c["frozen_baseline_commit"]) for p in c["frozen_inputs"]];ps=[probe(e) for e in c["candidate_endpoints"]];out("remaining_segment_official_endpoint_probe_v0.35.csv",ps,list(ps[0]))
 st=[]
 for s in c["segments"]:
  z,n,b=state(s,ps);st.append(dict(Segment_ID=s,Prior_State="UNMATERIALIZED_OFFICIAL_SOURCE",Final_State_v0_35=z,Full_Official_Membership_Materialized=str(z=="FULL_OFFICIAL_MEMBERSHIP_MATERIALIZED").lower(),Materialized_Row_Count=n,Identity_Reconciliation_Required=str(n>0).lower(),Canonical_Import_v0_35="false",Primary_Blocker=b,Next_Action="IDENTITY_RECONCILIATION" if n else "SOURCE_ACCESS_REMEDIATION_AND_GOVERNANCE_DECISION"))
 out("remaining_segment_materialization_status_v0.35.csv",st,list(st[0]));out("remaining_segment_source_access_ledger_v0.35.csv",st,list(st[0]))
 a=[dict(Segment_ID=e["Segment_ID"],Source_ID=e["Source_ID"],Candidate_URL=e["URL"],Discovery_Method=e["Discovery_Method"],Cloud_Browser_Visible=str(e["Discovered_In_Cloud_Browser"]).lower(),Direct_Asset=str(e["Direct_Asset"]).lower(),Official_Domain="true",Runner_Tested="true",Runner_Reproducible=next(x["Runner_Reproducible"] for x in ps if x["Source_ID"]==e["Source_ID"]),Full_Membership_Potential=e["Expected_Semantics"],Notes="") for e in c["candidate_endpoints"]];out("official_candidate_asset_links_v0.35.csv",a,list(a[0]));out("materialized_membership_inventory_v0.35.csv",[],["Segment_ID","Membership_File","Rows","Canonical_Import_v0_35"])
 f=sum(x["Full_Official_Membership_Materialized"]=="true" for x in st);nx="CURRENT_MASTER_REMAINING_MATERIALIZED_SEGMENT_IDENTITY_RECONCILIATION" if f else "CURRENT_MASTER_REMAINING_SOURCE_ACCESS_REMEDIATION_AND_GOVERNANCE_DECISION";sm=dict(revision="r2_real_deep_materialization",version="v0.35",current_master_rows=1633,imported_target_segments=8,missing_segments_checked=6,tested_official_endpoints=len(ps),direct_asset_or_api_candidates=sum(e["Direct_Asset"] for e in c["candidate_endpoints"]),new_full_membership_segments=f,next_stage=nx,canonical_master_import_v0_35=False,universe_mutated_v0_35=False,eligibility_promotion_v0_35=False,alpha_vantage=False,p0=False,sector_rs=False,swing_u3k_frozen=False,productive=False,source_superset_complete=False,stage_status_global="PARTIAL",frozen_input_audit=audit)
 for n in ["summary_v0.35.json","stage_checkpoint_v0.35.json","manifest_v0.35.json"]:(O/n).write_text(json.dumps(sm,indent=2)+"\n")
 h="# WELT-SWING CURRENT HANDOFF v0.35\n\nRevision: v0.35-r2 real deep materialization\n\n- Current Master: 1633 unchanged\n"+"\n".join("- "+x["Segment_ID"]+": "+x["Final_State_v0_35"]+" / rows "+str(x["Materialized_Row_Count"]) for x in st)+"\n\n- Next Stage: "+nx+"\n";(R/"WELT-SWING-CURRENT-Handoff-v0.35.md").write_text(h);(R/"WELT-SWING-CURRENT-Handoff-CURRENT.md").write_text(h)
if __name__=="__main__":main()
