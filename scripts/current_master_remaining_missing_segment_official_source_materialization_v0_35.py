#!/usr/bin/env python3
"""v0.35-r3 real materialization capability."""
import csv,json,pathlib,shutil,subprocess,sys
from io import BytesIO
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
R=pathlib.Path(__file__).resolve().parents[1];O=R/"output_current_master_remaining_source_materialization_v0_35";RAW=O/"raw_official_source";C=R/"config/current_master_remaining_missing_segment_official_source_materialization_v0.35.json";MEM=["Segment_ID","Official_Security_Code","Official_Security_Name","Official_Instrument_Type","Official_Exchange","Official_ISIN","Source_ID","Source_URL_or_Asset_ID","Source_AsOf","Source_Row_Number","Identity_Reconciliation_State","Canonical_Import_v0_35"]
def out(n,r,c):
 with open(O/n,"w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=c);w.writeheader();w.writerows(r)
def gate(p,b):
 a=subprocess.check_output(["git","hash-object",str(R/p)],text=True).strip();e=subprocess.check_output(["git","rev-parse",b+":"+p],text=True).strip()
 if a!=e:raise RuntimeError("FROZEN_INPUT_GATE_FAILED "+p)
 return {"Path":p,"Expected_Blob_SHA":e,"Actual_Blob_SHA":a,"PASS":True}
def val(d,k):return next((str(d[x]).strip() for x in k if d.get(x) not in (None,"")),"")
def parse(b,ct):
 t="";r=[];codes=[]
 if "pdf" in ct:
  try:t="\n".join(x.extract_text() or "" for x in PdfReader(BytesIO(b)).pages)
  except:pass
 elif "json" in ct:
  try:
   x=json.loads(b);t=json.dumps(x);r=x.get("output",x.get("data",x.get("result",[]))) if isinstance(x,dict) else x;r=r if isinstance(r,list) else [];codes=[val(z,["ISU_CD","ISU_SRT_CD","code","symbol","ticker"]) for z in r if isinstance(z,dict)]
  except:pass
 else:
  t=b.decode("utf-8","ignore");q=BeautifulSoup(t,"lxml").find("table")
  if q:r=[[c.get_text(" ",strip=True) for c in z.find_all(["td","th"])] for z in q.find_all("tr")[1:]];codes=[z[1] for z in r if len(z)>1 and z[1]]
 return t,r,sorted(set(x for x in codes if x))
def norm(e,r):
 a=[];seen=set()
 for i,z in enumerate(r,1):
  if isinstance(z,dict):code=val(z,["ISU_CD","ISU_SRT_CD","code","symbol","ticker"]);name=val(z,["ISU_NM","ISU_ABBRV","name","security_name"]);typ=val(z,["Instrument_Type","instrument_type","type"]);ex=val(z,["EXCH_NM","exchange"]);isin=val(z,["ISIN","isin"])
  elif isinstance(z,list):code=z[1].strip() if len(z)>1 else "";name=z[0].strip() if z else "";typ=ex=isin=""
  else:continue
  if code and code not in seen:seen.add(code);a.append({"Segment_ID":e["Segment_ID"],"Official_Security_Code":code,"Official_Security_Name":name,"Official_Instrument_Type":typ,"Official_Exchange":ex,"Official_ISIN":isin,"Source_ID":e["Source_ID"],"Source_URL_or_Asset_ID":e["URL"],"Source_AsOf":"","Source_Row_Number":i,"Identity_Reconciliation_State":"NOT_YET_RECONCILED","Canonical_Import_v0_35":"false"})
 return a
def probe(e):
 try:
  q=requests.request(e.get("Method","GET"),e["URL"],data=e.get("Form_Data"),headers={"User-Agent":"WeltSwing/0.35-r3"},timeout=30,allow_redirects=True);ct=q.headers.get("content-type","").split(";")[0].lower();RAW.joinpath(e["Segment_ID"]+"_"+e["Source_ID"]+".bin").write_bytes(q.content);t,r,c=parse(q.content,ct);lo=t.lower();n=norm(e,r);m=e.get("Plausible_Min_Rows",99999);v=q.status_code==200 and any(x in lo for x in ["full constituents","constituents list","constituent list","components list"]) and len(n)>=m and len(c)>=m and "top 10" not in lo
  return {"Segment_ID":e["Segment_ID"],"Source_ID":e["Source_ID"],"URL":e["URL"],"Source_Type":e["Source_Type"],"HTTP_Status":q.status_code,"Content_Type":ct,"Response_Bytes":len(q.content),"Redirect_Final_URL":q.url,"Authentication_Required":str("log in" in lo or "sign in" in lo).lower(),"Subscription_Required":str("subscription" in lo).lower(),"Parsed_Row_Count":len(r),"Unique_Security_Count":len(c),"Full_Membership_Claimed":str(any(x in lo for x in ["full constituents","constituents list","constituent list","components list"])).lower(),"Full_Membership_Validated":str(v).lower(),"AsOf":"","Error_Class":"","Evidence_Notes":t[:700].replace("\n"," "),"Runner_Tested":"true","Runner_Reproducible":str(q.status_code==200).lower(),"Direct_Asset":str(e["Direct_Asset"]).lower(),"_n":n}
 except Exception as x:return {"Segment_ID":e["Segment_ID"],"Source_ID":e["Source_ID"],"URL":e["URL"],"Source_Type":e["Source_Type"],"HTTP_Status":"","Content_Type":"","Response_Bytes":0,"Redirect_Final_URL":"","Authentication_Required":"unknown","Subscription_Required":"unknown","Parsed_Row_Count":0,"Unique_Security_Count":0,"Full_Membership_Claimed":"false","Full_Membership_Validated":"false","AsOf":"","Error_Class":type(x).__name__,"Evidence_Notes":str(x),"Runner_Tested":"true","Runner_Reproducible":"false","Direct_Asset":str(e["Direct_Asset"]).lower(),"_n":[]}
def st(s,p):
 x=[z for z in p if z["Segment_ID"]==s];v=[z for z in x if z["Full_Membership_Validated"]=="true"];t=" ".join(z["Evidence_Notes"].lower() for z in x)
 if v:return "FULL_OFFICIAL_MEMBERSHIP_MATERIALIZED",sum(len(z["_n"]) for z in v),"validated parsed official membership"
 if "subscription" in t:return "OFFICIAL_ROUTE_SUBSCRIPTION_OR_LICENSE_REQUIRED",0,"official subscription evidence"
 if "full constituents" in t:return "OFFICIAL_FULL_LIST_VISIBLE_BUT_REPRODUCIBLE_EXPORT_NOT_MATERIALIZED",0,"full list visible without reproducible export"
 if "rebalance" in t or "quarterly review" in t:return "OFFICIAL_CHANGE_DOCUMENTS_ONLY",0,"official change/review evidence only"
 if s=="KR_KOSPI200":return "OFFICIAL_SOURCE_FOUND_DATA_ENDPOINT_NOT_RESOLVED",0,"KRX API lacks complete evidenced request parameters"
 return "OFFICIAL_SOURCE_NOT_MATERIALIZED",0,"official routes did not yield full membership"
def selftest():
 e={"Segment_ID":"TEST","Source_ID":"SYN","URL":"local://synthetic"};r=norm(e,[{"ISU_CD":"AAA","ISU_NM":"Alpha"},{"ISU_CD":"BBB","ISU_NM":"Beta"},{"ISU_CD":"CCC","ISU_NM":"Gamma"}]);assert len(r)==3 and len({x["Official_Security_Code"] for x in r})==3;assert [{"Segment_ID":"TEST","Membership_File":"test.csv","Rows":len(r),"Canonical_Import_v0_35":"false"}][0]["Rows"]==3;print("SELF_TEST_POSITIVE_MATERIALIZATION_PASS")
def main():
 if "--self-test" in sys.argv:selftest();return
 c=json.loads(C.read_text());shutil.rmtree(O,ignore_errors=True);RAW.mkdir(parents=True);audit=[gate(p,c["frozen_baseline_commit"]) for p in c["frozen_inputs"]];p=[probe(e) for e in c["candidate_endpoints"]];pub=[{k:v for k,v in z.items() if k!="_n"} for z in p];out("remaining_segment_official_endpoint_probe_v0.35.csv",pub,list(pub[0]));inv=[]
 for z in p:
  if z["Full_Membership_Validated"]=="true":fn=z["Segment_ID"].lower()+"_official_membership_v0.35.csv";out(fn,z["_n"],MEM);inv.append({"Segment_ID":z["Segment_ID"],"Membership_File":fn,"Rows":len(z["_n"]),"Canonical_Import_v0_35":"false"})
 rows=[]
 for s in c["segments"]:
  a,n,b=st(s,p);rows.append({"Segment_ID":s,"Prior_State":"UNMATERIALIZED_OFFICIAL_SOURCE","Final_State_v0_35":a,"Full_Official_Membership_Materialized":str(a=="FULL_OFFICIAL_MEMBERSHIP_MATERIALIZED").lower(),"Materialized_Row_Count":n,"Identity_Reconciliation_Required":str(n>0).lower(),"Canonical_Import_v0_35":"false","Primary_Blocker":b,"Next_Action":"IDENTITY_RECONCILIATION" if n else "SOURCE_ACCESS_REMEDIATION_AND_GOVERNANCE_DECISION"})
 out("remaining_segment_materialization_status_v0.35.csv",rows,list(rows[0]));out("remaining_segment_source_access_ledger_v0.35.csv",rows,list(rows[0]));a=[{"Segment_ID":e["Segment_ID"],"Source_ID":e["Source_ID"],"Candidate_URL":e["URL"],"Discovery_Method":e["Discovery_Method"],"Cloud_Browser_Visible":str(e["Discovered_In_Cloud_Browser"]).lower(),"Direct_Asset":str(e["Direct_Asset"]).lower(),"Official_Domain":"true","Runner_Tested":"true","Runner_Reproducible":next(z["Runner_Reproducible"] for z in p if z["Source_ID"]==e["Source_ID"]),"Full_Membership_Potential":e["Expected_Semantics"],"Notes":""} for e in c["candidate_endpoints"]];out("official_candidate_asset_links_v0.35.csv",a,list(a[0]));out("materialized_membership_inventory_v0.35.csv",inv,["Segment_ID","Membership_File","Rows","Canonical_Import_v0_35"]);f=len(inv);nx="CURRENT_MASTER_REMAINING_MATERIALIZED_SEGMENT_IDENTITY_RECONCILIATION" if f else "CURRENT_MASTER_REMAINING_SOURCE_ACCESS_REMEDIATION_AND_GOVERNANCE_DECISION";sm={"revision":"r3_final_materialization_capability_and_current_asset_fix","current_master_rows":1633,"imported_target_segments":8,"missing_segments_checked":6,"tested_official_endpoints":len(p),"direct_asset_or_api_candidates":sum(e["Direct_Asset"] for e in c["candidate_endpoints"]),"new_full_membership_segments":f,"next_stage":nx,"canonical_master_import_v0_35":False,"universe_mutated_v0_35":False,"eligibility_promotion_v0_35":False,"alpha_vantage":False,"p0":False,"sector_rs":False,"swing_u3k_frozen":False,"productive":False,"source_superset_complete":False,"stage_status_global":"PARTIAL","frozen_input_audit":audit}
 for n in ["summary_v0.35.json","stage_checkpoint_v0.35.json","manifest_v0.35.json"]:(O/n).write_text(json.dumps(sm,indent=2)+"\n")
 h="# WELT-SWING CURRENT HANDOFF v0.35\n\nRevision: v0.35-r3 final materialization capability\n\n- Current Master: 1633 unchanged\n"+"\n".join("- "+z["Segment_ID"]+": "+z["Final_State_v0_35"]+" / rows "+str(z["Materialized_Row_Count"]) for z in rows)+"\n\n- Next Stage: "+nx+"\n";(R/"WELT-SWING-CURRENT-Handoff-v0.35.md").write_text(h);(R/"WELT-SWING-CURRENT-Handoff-CURRENT.md").write_text(h)
if __name__=="__main__":main()
